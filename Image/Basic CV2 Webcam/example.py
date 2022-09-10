# import computer vision library(cv2) in this code
import cv2
import sys
# main code
if __name__ == "__main__" :
 
    # creating a video capture object
    # argument 0 , webcam start
    video_object = cv2.VideoCapture(0)
 
    # handling errors
    # if any erros is occured during the running of the program
    # then it handles
    try :
        # run a infinite loop
        while(True) :
 
            # read a video frame by frame
            # read() returns tuple in which 1st item is boolean value
            # either True or False and 2nd item is frame of the video.
            # read() returns False when live video is ended so
            # no frame is readed and error will be generated.
            ret,frame = video_object.read()
            
            # show the frame on the newly created image window
            cv2.imshow('Frames',frame)
 
            # this condition is used to run a frames at the interval of 10 mili sec
            # and if in b/w the frame running , any one want to stop the execution .
            if cv2.waitKey(10) & 0xFF == ord('q') :
 
                # break out of the while loop
                break
 
    except :
        # if error occur then this block of code is run
        print("Video has ended..")