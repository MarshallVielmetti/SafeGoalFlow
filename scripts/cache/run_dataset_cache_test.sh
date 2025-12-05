# export LD_LIBRARY_PATH="/usr/local/cuda/lib64"
# The trajectory_sampling.time_horizon in trainval is 5
CACHE_TO_SAVE='' # set your feature cache path to save (leave empty to use NAVSIM_EXP_ROOT or $HOME/.goalflow)

CACHE_TO_SAVE=$NAVSIM_EXP_ROOT/training_cache

echo $CACHE_TO_SAVE

python ./navsim/planning/script/run_dataset_caching.py \
agent=goalflow_agent_traj \
agent.config.trajectory_sampling.time_horizon=5 \
experiment_name=a_goalflow_test_cache \
cache_path=$CACHE_TO_SAVE \
scene_filter=navtest \
split=test
