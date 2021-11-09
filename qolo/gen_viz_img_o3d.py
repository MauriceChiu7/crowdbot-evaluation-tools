# -*-coding:utf-8 -*-
'''
@File    :   gen_viz_img_o3d.py
@Time    :   2021/10/26
@Author  :   Yujie He
@Version :   1.0
@Contact :   yujie.he@epfl.ch
@State   :   Dev
'''


import os
import argparse
import numpy as np
from crowdbot_data import AllFrames
from o3d_viz_util import plot_robot_frame_o3d, plot_world_frame_o3d

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='convert data from rosbag')
    
    parser.add_argument('-b', '--base', default='/home/crowdbot/Documents/yujie/crowdbot_tools', type=str,
                        help='base folder, i.e., the path of the current workspace')
    parser.add_argument('-d', '--data', default='data', type=str,
                        help='data folder, i.e., the name of folder that stored extracted raw data and processed data')
    parser.add_argument('-f', '--folder', default='nocam_rosbags', type=str,
                        help='different subfolder in rosbag/ dir')
    args = parser.parse_args()

    allf = AllFrames(args)


    for seq_idx in range(allf.nr_seqs()):

        seq = allf.seqs[seq_idx]
        print("({}/{}): {} with {} frames".format(seq_idx+1, allf.nr_seqs(), seq, allf.nr_frames(seq_idx)))

        # seq dest: data/xxxx_processed/viz_imgs/seq
        img_seq_dir = os.path.join(allf.imgs_dir, seq)

        if not os.path.exists(img_seq_dir):
            print("Images will be saved in {}".format(img_seq_dir))
            os.makedirs(img_seq_dir, exist_ok=True)

            # TODO: create new pose_stamped based visualization
            consider_pose = True
            if consider_pose:
                qolo_tf_dir = os.path.join(allf.source_data_dir, "qolo_tf")
                lidar_stamped_path = os.path.join(qolo_tf_dir, seq+'_lidar_pose_stamped.npy')
                lidar_pose_stamped = np.load(lidar_stamped_path, allow_pickle=True).item()

            # generate image every step_viz frames
            step_viz = 4
            for fr_idx in range(0, allf.nr_frames(seq_idx), step_viz):
                # !!! consider pose_stamped
                # input a series of poses
                if consider_pose:
                    trans = lidar_pose_stamped['position'][:fr_idx+1]
                    rot_quat = lidar_pose_stamped['orientation'][:fr_idx+1]
                # input single pose
                # trans = lidar_pose_stamped['position'][fr_idx]
                # rot_quat = lidar_pose_stamped['orientation'][fr_idx]

                lidar, dets, dets_conf, trks = allf[seq_idx, fr_idx]
                # fig = plot_frame(lidar, trks, f"./tmp/{fr_idx}.png")
                # figpath = os.path.join(img_seq_dir, str(fr_idx)+".png")
                figpath = os.path.join(img_seq_dir, "{0:04d}.png".format(fr_idx))
                # fig = plot_frame(lidar, trks, figpath)
                # mlab.close(fig)
                # print(len(lidar), len(lidar[0]))
                print("({}/{}): {:1f}% remaining"
                      .format(fr_idx//step_viz+1, 
                              allf.nr_frames(seq_idx)//step_viz+1,
                              100-(50*fr_idx+100)/(allf.nr_frames(seq_idx)//2+1)))
                
                # !!! consider pose_stamped
                if consider_pose:
                    plot_world_frame_o3d(lidar.T, (trans, rot_quat), trks, figpath)
                else:
                    plot_robot_frame_o3d(lidar.T, trks, figpath)
        else:
            print("{} images already generated!!!".format(allf.seqs[seq_idx]))
            continue

