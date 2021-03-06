import csv
import json
import os
import sys
import time

import cv2
import numpy as np

def takeKey(elem):
    return elem[0][-1]

def track(video_path, finger, corner, frame_no):
    # Read video
    video = cv2.VideoCapture(str(video_path))

    # Exit if video not opened.
    if not video.isOpened():
        print("Could not open video")
        sys.exit()
    # Read first frame.
    while frame_no >= 0:
        ok, frame = video.read()
        if not ok:
            print('Cannot read video file')
            sys.exit()
        frame_no -= 1
    finger_box = tuple([int(finger[1]), int(finger[2]), 20, 20])
    phone_box = tuple(
        [int((int(corner[0]) + int(corner[2])) / 2 - 10), int((int(corner[1]) + int(corner[3])) / 2 - 10), 20, 20])

    X = []
    Y = []

    np.array(X)
    np.array(Y)

    finger_center = (int(finger_box[0] + finger_box[2] / 2), int(finger_box[1] + finger_box[3] / 2))
    phone_center = (int(phone_box[0] + phone_box[2] / 2), int(phone_box[1] + phone_box[3] / 2))
    X.append(finger_center[0] - phone_center[0])
    Y.append(finger_center[1] - phone_center[1])

    # Set up tracker.
    finger_tracker = cv2.TrackerCSRT_create()
    phone_tracker = cv2.TrackerCSRT_create()

    finger_ok = finger_tracker.init(frame, finger_box)
    phone_ok = phone_tracker.init(frame, phone_box)


    while True:
        # Read a new frame
        ok, frame = video.read()
        if not ok:
            break

        # Start timer
        timer = cv2.getTickCount()

        # Update tracker
        finger_ok, finger_box = finger_tracker.update(frame)
        phone_ok, phone_box = phone_tracker.update(frame)

        # Calculate Frames per second (FPS)
        fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);

        # Draw bounding box
        if finger_ok :
            # Tracking success
            p1 = (int(finger_box[0]), int(finger_box[1]))
            p2 = (int(finger_box[0] + finger_box[2]), int(finger_box[1] + finger_box[3]))
            p3 = (int(phone_box[0]), int(phone_box[1]))
            p4 = (int(phone_box[0] + phone_box[2]), int(phone_box[1] + phone_box[3]))
            cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
            cv2.rectangle(frame, p3, p4, (255,0,0), 2, 1)
            finger_center = (int(finger_box[0] + finger_box[2] / 2), int(finger_box[1] + finger_box[3] / 2))
            phone_center = (int(phone_box[0] + phone_box[2] / 2), int(phone_box[1] + phone_box[3] / 2))
            # X.append(finger_center[0])
            # Y.append(finger_center[1])
            X.append(finger_center[0]-phone_center[0])
            Y.append(finger_center[1]-phone_center[1])
            if len(X) > 1 and (abs(X[-1] - X[-2]) > 100 or abs(Y[-1] - Y[-2]) > 100):
                X.pop()
                Y.pop()
                break
        else:
            # Tracking failure
            cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)

        # Display tracker type on frame
        cv2.putText(frame, "CSRT" + " Tracker", (100,20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50),2);

        # Display FPS on frame
        cv2.putText(frame, "FPS : " + str(int(fps)), (100,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2);

        cv2.imshow("Tracking", frame)

        # Exit if ESC pressed
        k = cv2.waitKey(1) & 0xff
        if k == 27 : break
    video.release()
    return (X, Y)

for file in os.listdir("results/s1/double_hand"):
    if file.split('.')[-1] == 'txt':
        file = 'data/s1/' + file.split('.')[0] + '.MOV'
    else:
        continue
    # if file != 'data/s1/SSSM-B3-00033.MOV':
    #     continue
    print(file)
    nFrames = 60 #检测的帧数量

    name = str(file).split("/")[-1].split(".")[0]

    direction_res = "results/s1/direction/"

    corner_res = "results/s1/corner/"

    hand_res = "results/s1/double_hand/"

    hands = open(hand_res+name+".txt").read().split('\n')[:-1]
    frame_nos = [] # 记录所有帧号
    for i in range(len(hands)):
        hands[i] = hands[i].split()
        if int(hands[i][0]) < nFrames:
            hands[i][0] = int(hands[i][0])
            frame_nos.append(hands[i][0])
            hands[i][3] = float(hands[i][3])
        else:
            break

    hands = hands[:i]
    if len(list(set(frame_nos))) == len(frame_nos):
        only_one_hand = True
    else:
        only_one_hand = False

    detection_results = []
    i = 0
    while i < nFrames:
        pic_name = name+"_"+str(i)

        with open(corner_res+pic_name+".txt",'r') as f:
            corner = f.readline()[1:-1].split()

        #判断是否检测到
        if len(corner)< 4:
            i = i + 1
            continue
        finger = []
        for j in range(len(hands)):
            if hands[j][0] == i:
                finger += hands[j]
        if only_one_hand and finger:
            detection_results.append([finger,corner])
        else:
            if len(finger) != 8:
                i = i + 1
                continue
            else:
                finger.append(finger[3] + finger[7])
                detection_results.append([finger,corner])#保存手部关键点和手机角

        i += 1


    detection_results.sort(key = takeKey,reverse = True)

    dresult = detection_results[0]

    frame_no = int(dresult[0][0])

    finger = dresult[0][0:4]
    corner = dresult[1]

    threshold = 5
    X, Y = track(file, finger, corner, frame_no)
    if max(X) - min(X) < threshold:
        if only_one_hand:
            print("There is no right hand in the video.")
        else:
            finger = dresult[0][4:8]
            X, Y = track(file, finger, corner, frame_no)
    rows= []
    direction = open(direction_res+name+".txt").readline()

    if direction == '1':
        for i in range(len(X)):
            row = {"frame":i,"X":X[i]-X[0],"Y":Y[0]-Y[i]}
            rows.append(row)
    elif direction == '2':
        for i in range(len(X)):
            row = {"frame":i,"X":Y[i]-Y[0],"Y":X[i]-X[0]}
            rows.append(row)
    elif direction == '3':
        for i in range(len(X)):
            row = {"frame":i,"X":X[0]-X[i],"Y":Y[i]-Y[0]}
            rows.append(row)
    elif direction == '4':
        for i in range(len(X)):
            row = {"frame":i,"X":Y[0]-Y[i],"Y":X[0]-X[i]}
            rows.append(row)

    res_path = "results/s1/track/double_hand/"+name
    if not os.path.exists(res_path):
        os.mkdir(res_path)


    with open("results/s1/track/double_hand/"+name+"/raw_trajectory.csv","w") as f:
        rst_csv = csv.DictWriter(f,["frame","X","Y"])
        rst_csv.writeheader()
        rst_csv.writerows(rows)

    cv2.destroyAllWindows()
