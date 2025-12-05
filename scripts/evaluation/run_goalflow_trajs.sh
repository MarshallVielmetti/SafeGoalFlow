# export LD_LIBRARY_PATH="/usr/local/cuda/lib64"
# export HYDRA_FULL_ERROR=1

SPLIT=test
METRIC_CACHE=$GOALFLOW_DIR/exp/metric_cache # set your metric path
# TRAJS_CACHE="${GOALFLOW_DIR}/exp/a_test_release/2025.12.04.12.04.20/lightning_logs/version_0/trajs" # set your trajectories path
# TRAJS_CACHE="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.16.01.12/lightning_logs/version_0/trajs"
# TRAJS_CACHE="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.18.15.58/lightning_logs/version_0/trajs" # small batch of 10
# TRAJS_CACHE="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.18.40.29/lightning_logs/version_0/trajs" # set of 100
TRAJS_CACHE="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.19.36.20/lightning_logs/version_0/trajs" # FULL RUN!
CHECKPOINT=$GOALFLOW_DIR/data/goalflow_traj_epoch_54-step_18260.ckpt

echo $METRIC_CACHE
echo $TRAJS_CACHE
echo $CHECKPOINT

python $NAVSIM_DEVKIT_ROOT/planning/script/run_pdm_score_trajs.py \
agent=goalflow_agent_traj \
"agent.checkpoint_path=$CHECKPOINT" \
experiment_name=a_test_release_result \
scene_filter=navtest \
"split=$SPLIT" \
"metric_cache_path=$METRIC_CACHE" \
"trajs_cache_path=$TRAJS_CACHE" \

# python $NAVSIM_DEVKIT_ROOT/planning/script/run_pdm_score_trajs.py \
# agent=goalflow_agent_traj \
# "agent.checkpoint_path=$CHECKPOINT" \
# experiment_name=a_test_release_result \
# scene_filter=navtest \
# "split=$SPLIT" \
# "metric_cache_path=$METRIC_CACHE" \
# "trajs_cache_path=$TRAJS_CACHE" \