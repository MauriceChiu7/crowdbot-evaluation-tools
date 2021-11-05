# -*-coding:utf-8 -*-
'''
@File    :   gen_crowd_eval.py
@Time    :   2021/11/02
@Author  :   Yujie He
@Version :   1.0
@Contact :   yujie.he@epfl.ch
@State   :   Dev
'''

"""
evaluate the min. dist. from qolo and crowd density within 10m of qolo and save corresponding images
TODO: compare with detected pedestrain from the rosbag!
TODO: separate the plotting code into a independent part in eval/
TODO: read /rds_to_gui in `rds_network_ros/ToGui` to get start timestamp and stoptimestamp
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from crowdbot_data import AllFrames

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='convert data from rosbag')
    
    parser.add_argument('-b', '--base', default='/home/crowdbot/Documents/yujie/crowdbot_tools', type=str,
                        help='base folder, i.e., the path of the current workspace')
    parser.add_argument('-d', '--data', default='data', type=str,
                        help='data folder, i.e., the name of folder that stored extracted raw data and processed data')
    parser.add_argument('-f', '--folder', default='nocam_rosbags', type=str,
                        help='different subfolder in rosbag/ dir')
    # parser.add_argument('--dist', default=10., type=float, nargs='+', 
    #                     help='considered distance(s) in density evaluation')
    # directly set limitation as [5, 10]
    parser.add_argument('--save_img', dest='save_img', action='store_true',
                        help='plot and save crowd density image')
    parser.set_defaults(save_img=True)
    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help="Whether to overwrite existing rosbags (default: false)")
    parser.set_defaults(feature=False)
    args = parser.parse_args()

    allf = AllFrames(args)

    print("Starting extracting crowd_density files from {} rosbags!".format(allf.nr_seqs()))

    eval_res_dir = os.path.join(allf.metrics_dir)
    twist_dir = os.path.join(allf.source_data_dir, 'twist')

    if not os.path.exists(eval_res_dir):
        print("Crowd density images and npy will be saved in {}".format(eval_res_dir))
        os.makedirs(eval_res_dir, exist_ok=True)

    if not os.path.exists(twist_dir):
        print("ERROR: Please extract twist_stamped by using gen_twist_ts")

    for seq_idx in range(allf.nr_seqs()):

        seq = allf.seqs[seq_idx]
        print("({}/{}): {} with {} frames".format(seq_idx+1, allf.nr_seqs(), seq, allf.nr_frames(seq_idx)))

        # source
        source_twist_path = os.path.join(twist_dir, seq+'_twist_stamped.npy')
        source_twist = np.load(source_twist_path, allow_pickle=True).item()
        # print(source_twist.get("x")[1:200:5])
        # print(source_twist.get("zrot")[1:200:5])
        # starting: larger than zero
        start_idx = np.min([np.min(np.nonzero(source_twist.get("x"))), 
                           np.min(np.nonzero(source_twist.get("zrot")))])
        start_ts = source_twist.get("timestamp")[start_idx]
        print("starting timestamp: {}".format(start_ts))
        # TODO: extract end which is closet to the goal within a distance
        # TODO: consider adding a threshold


        # dest
        crowd_eval_npy = os.path.join(eval_res_dir, seq+'_crowd_eval.npy')

        if (not os.path.exists(crowd_eval_npy)) or (args.overwrite):

            # timestamp can be read from lidars/ folder
            stamp_file_path = os.path.join(allf.lidar_dir, seq+'_stamped.npy')
            lidar_stamped_dict = np.load(stamp_file_path, allow_pickle=True)
            ts_np = lidar_stamped_dict.item().get('timestamp')
            all_det_list = []
            within_det5_list = []
            within_det10_list = []
            min_dist_list = []
            crowd_density5_list = []
            crowd_density10_list = []

            for fr_idx in range(allf.nr_frames(seq_idx)):

                _, _, _, trks = allf[seq_idx, fr_idx]

                # 1. all_det
                all_det = np.shape(trks)[0]

                # 2. within_det
                # r_square_within = (trks[:,0]**2 + trks[:,1]**2) < args.dist**2
                # within_det = np.shape(trks[r_square_within,:])[0]
                all_dist = np.linalg.norm(trks[:,[0,1]], axis=1)
                within_det5 = np.sum(np.less(all_dist, 5.0))
                within_det10 = np.sum(np.less(all_dist, 10.0))
                print("Seq {}/{} - Frame {}/{}: filtered/overall boxes within 10m: {}/{}"
                      .format(seq_idx+1, allf.nr_seqs(),
                              fr_idx+1, allf.nr_frames(seq_idx), 
                              within_det10, all_det))

                # 3. min_dist
                # b = np.random.rand(5,3)
                # b01_norm = np.linalg.norm(b[:,[0,1]], axis=1)
                min_dist = min(all_dist)

                # 4. crowd_density
                area_local5 = np.pi*5.0**2
                crowd_density5 = within_det5/area_local5
                area_local10 = np.pi*10.0**2
                crowd_density10 = within_det10/area_local10

                # append into list
                all_det_list.append(all_det)
                within_det5_list.append(within_det5)
                within_det10_list.append(within_det10)
                min_dist_list.append(min_dist)
                crowd_density5_list.append(crowd_density5)
                crowd_density10_list.append(crowd_density10)

            ad_np = np.asarray(all_det_list, dtype=np.uint8)
            wd5_np = np.asarray(within_det5_list, dtype=np.uint8)
            wd10_np = np.asarray(within_det10_list, dtype=np.uint8)
            md_np = np.asarray(min_dist_list, dtype=np.float32)
            cd5_np = np.asarray(crowd_density5_list, dtype=np.float32)
            cd10_np = np.asarray(crowd_density10_list, dtype=np.float32)
            crowd_eval_dict = {'timestamp': ts_np, 
                            'all_det': ad_np, 
                            'within_det5': wd5_np, 
                            'within_det10': wd10_np, 
                            'min_dist': md_np, 
                            'crowd_density5': cd5_np,
                            'crowd_density10': cd10_np}
            np.save(crowd_eval_npy, crowd_eval_dict)

            if args.save_img:
                # figure1: crowd density
                fig, ax = plt.subplots(figsize=(8, 4))

                l1, = ax.plot(ts_np-np.min(ts_np), cd5_np, linewidth=1, color='coral', label='x = 5')
                l2, = ax.plot(ts_np-np.min(ts_np), cd10_np, linewidth=1, color='navy', label='x = 10')

                ax.legend(handles=[l1, l2])
                ax.set_title("Crowd Density within x [m] of qolo", fontsize=15)
                _ = ax.set_xlabel("t [s]")
                _ = ax.set_ylabel("Density [1/m^2]")

                ax.set_xlim(left=0.0)
                ax.set_ylim(bottom=0.0)

                fig.tight_layout()
                cd_img_path = os.path.join(eval_res_dir, seq+'_crowd_density.png')
                plt.savefig(cd_img_path, dpi=300) # png, pdf

                # figure2: min. dist.
                fig2, ax2 = plt.subplots(figsize=(8, 4))

                ax2.plot(ts_np-np.min(ts_np), md_np, linewidth=1, color='coral')
                ax2.axhline(y=0.3, xmin=0.0, xmax=np.max(ts_np)-np.min(ts_np), linestyle='--', color='navy')

                ax2.set_title("Min. Distance of Pedestrain from qolo", fontsize=15)
                _ = ax2.set_xlabel("t [s]")
                _ = ax2.set_ylabel("Distance [m]")
                
                ax2.set_xlim(left=0.0)
                ax2.set_ylim(bottom=0.0, top=5.0)

                fig2.tight_layout()
                md_img_path = os.path.join(eval_res_dir, seq+'_min_dist.png')
                plt.savefig(md_img_path, dpi=300) # png, pdf
        else:
            print("Crowd density of {} already generated!!!".format(seq))
            continue