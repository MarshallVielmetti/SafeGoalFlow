import torch
import torch.nn as nn
import torch.nn.functional as F


class SafetyBarrier(nn.Module):
    def __init__(self, pixel_size=0.25, ego_radius=2.5, bev_range=32.0):
        """
        Args:
            pixel_size: meters per pixel (default 0.25 from GoalFlowConfig)
            ego_radius: ego vehicle radius in meters
            bev_range: BEV range in meters (default 32m, matching lidar_max_x/y)
        """
        super().__init__()
        self.pixel_size = pixel_size
        self.ego_radius = ego_radius
        self.bev_range = bev_range
        
    def compute_sdf(self, semantics: torch.Tensor, threshold=0.5):
        """
        Input: semantics [B, Classes, H, W] - Output from bev_semantic_head
        Output: sdf [B, 1, H, W] - Signed Distance Field
        
        Convention: h(x) > 0 means SAFE (inside drivable area with margin)
                    h(x) < 0 means UNSAFE (outside or too close to boundary)
        """
        from kornia.contrib import distance_transform
        
        # 1. Get Drivable Area (class 1 is road in GoalFlow's BEV semantic classes)
        # The BEV semantic head outputs logits for each class
        road_prob = torch.sigmoid(semantics[:, 1:2, :, :])  # Class 1 is road
        
        # 2. Binary Mask: 1 = drivable, 0 = non-drivable
        drivable_mask = (road_prob > threshold).float()
        non_drivable_mask = 1.0 - drivable_mask
        
        # 3. Compute distance transforms
        # distance_transform returns distance to nearest 0 in the input
        # For drivable mask: distance to nearest non-drivable (boundary)
        # For non-drivable mask: distance to nearest drivable
        dist_to_boundary = distance_transform(drivable_mask)      # positive inside drivable
        dist_to_drivable = distance_transform(non_drivable_mask)  # positive outside drivable
        
        # 4. Create signed distance field
        # Inside drivable: positive (distance to boundary)
        # Outside drivable: negative (distance to drivable area)
        sdf = dist_to_boundary - dist_to_drivable
        
        # 5. Convert to meters and subtract ego radius for safety margin
        # h(x) = distance_to_boundary - ego_radius
        # h(x) > 0 means we have clearance beyond ego radius
        sdf = sdf * self.pixel_size - self.ego_radius
        
        return sdf

    def get_gradients(self, sdf, trajs):
        """
        Sample SDF and gradients at trajectory points.
        
        Args:
            sdf: [B, 1, H, W] - Signed Distance Field
            trajs: [B, N, 2] - Trajectory points in metric coordinates
            
        Returns:
            h_val: [B, N, 1] - SDF values at trajectory points
            h_grad: [B, N, 2] - SDF gradients at trajectory points
        """
        B, N, _ = trajs.shape
        H, W = sdf.shape[-2:]
        
        # 1. Compute SDF gradients using Sobel filters (more stable than autograd)
        sobel_x = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], 
                               dtype=sdf.dtype, device=sdf.device).view(1, 1, 3, 3) / 8.0
        sobel_y = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], 
                               dtype=sdf.dtype, device=sdf.device).view(1, 1, 3, 3) / 8.0
        
        # Pad SDF for convolution
        sdf_padded = F.pad(sdf, (1, 1, 1, 1), mode='replicate')
        
        # Compute spatial gradients (in pixel space)
        grad_x_map = F.conv2d(sdf_padded, sobel_x)  # [B, 1, H, W] - gradient in image x direction
        grad_y_map = F.conv2d(sdf_padded, sobel_y)  # [B, 1, H, W] - gradient in image y direction
        
        # 2. Convert trajectory coordinates to grid coordinates
        grid_coords = self.metric_to_grid(trajs, H, W)
        grid_coords = grid_coords.unsqueeze(1)  # [B, 1, N, 2]
        
        # 3. Sample SDF values at trajectory points
        h_val = F.grid_sample(sdf, grid_coords, align_corners=True, 
                              mode='bilinear', padding_mode='border')  # [B, 1, 1, N]
        h_val = h_val.view(B, N, 1)
        
        # 4. Sample gradients at trajectory points
        grad_x_sampled = F.grid_sample(grad_x_map, grid_coords, align_corners=True,
                                       mode='bilinear', padding_mode='border')  # [B, 1, 1, N]
        grad_y_sampled = F.grid_sample(grad_y_map, grid_coords, align_corners=True,
                                       mode='bilinear', padding_mode='border')  # [B, 1, 1, N]
        
        # 5. Convert pixel gradients to metric gradients
        # Image x corresponds to metric y, image y corresponds to metric x
        # Scale by pixel_size to convert from per-pixel to per-meter
        grad_metric_x = grad_y_sampled.view(B, N, 1) / self.pixel_size  # forward direction
        grad_metric_y = grad_x_sampled.view(B, N, 1) / self.pixel_size  # lateral direction
        
        h_grad = torch.cat([grad_metric_x, grad_metric_y], dim=-1)  # [B, N, 2]
        
        return h_val, h_grad
    
    def metric_to_grid(self, trajs, H, W):
        """
        Convert metric coordinates to normalized grid coordinates [-1, 1] for grid_sample.
        
        In GoalFlow's BEV coordinate system:
        - Ego vehicle is at the center-bottom of the BEV (pixel coords: y=0, x=W/2)
        - X-axis (in metric): forward direction, maps to y-axis in image (0 to H)
        - Y-axis (in metric): lateral direction, maps to x-axis in image (0 to W)
        - Metric range: [-bev_range, bev_range] for both axes
        
        Args:
            trajs: [B, N, 2] trajectory points in metric coordinates (x=forward, y=lateral)
            H, W: height and width of the SDF map
            
        Returns:
            grid_coords: [B, N, 2] normalized coordinates in [-1, 1] for grid_sample
                         grid_sample expects (x, y) where x is horizontal and y is vertical
        """
        # trajs[..., 0] is forward (x in metric) -> maps to y in image
        # trajs[..., 1] is lateral (y in metric) -> maps to x in image
        
        # Convert metric to pixel coordinates
        # Forward (metric x) -> pixel y: ego is at y=0, forward is positive y
        pixel_y = trajs[..., 0] / self.pixel_size  # forward direction
        # Lateral (metric y) -> pixel x: ego is at x=W/2, left is negative x
        pixel_x = trajs[..., 1] / self.pixel_size + W / 2.0
        
        # Normalize to [-1, 1] for grid_sample
        # grid_sample expects (x, y) format where:
        # x=-1 is left edge, x=1 is right edge
        # y=-1 is top edge, y=1 is bottom edge
        norm_x = (pixel_x / (W - 1)) * 2 - 1  # [0, W-1] -> [-1, 1]
        norm_y = (pixel_y / (H - 1)) * 2 - 1  # [0, H-1] -> [-1, 1]
        
        # Clamp to valid range
        norm_x = torch.clamp(norm_x, -1, 1)
        norm_y = torch.clamp(norm_y, -1, 1)
        
        # Stack as (x, y) for grid_sample
        grid_coords = torch.stack([norm_x, norm_y], dim=-1)
        
        return grid_coords