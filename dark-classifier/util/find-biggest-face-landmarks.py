import sys
import dlib
import urllib2
from StringIO import StringIO
from skimage import io

def RectSize(rect):
	return (rect.bottom() - rect.top()) * (rect.right() - rect.left())

EXTEND = 20

# You can download the required pre-trained face detection model here:
# http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
predictor_model = "shape_predictor_68_face_landmarks.dat"

# Create a HOG face detector using the built-in dlib class
face_detector = dlib.get_frontal_face_detector()
face_pose_predictor = dlib.shape_predictor(predictor_model)

win = dlib.image_window()

# Take the image file name from the command line
file_name = sys.argv[1]

# Load the image
img_bytes = urllib2.urlopen(file_name).read()
image = io.imread(StringIO(img_bytes))
# image = io.imread(file_name)

height = image.shape[0]
width = image.shape[1]

# Run the HOG face detector on the image data
detected_faces = face_detector(image, 1)

print("Found {} faces in the image file {}".format(len(detected_faces), file_name))

# Show the desktop window with the image
win.set_image(image)

if len(detected_faces) > 0:
	biggest_index = 0
	biggest_rect_size = RectSize(detected_faces[0])

	for i in xrange(1, len(detected_faces)):
		rect_size = RectSize(detected_faces[i])
		if biggest_rect_size < rect_size:
			biggest_index = i
			biggest_rect_size = rect_size

	print biggest_index
	biggest_face = detected_faces[biggest_index]
	
	top = 0 if (biggest_face.top()-EXTEND) < 0 else (biggest_face.top()-EXTEND)
	bottom = height if (biggest_face.bottom()+EXTEND) > height else (biggest_face.bottom()+EXTEND)
	left = 0 if (biggest_face.left()-EXTEND) < 0 else (biggest_face.left()-EXTEND)
	right = width if (biggest_face.right()+EXTEND) > width else (biggest_face.right()+EXTEND)
	crop = image[top:bottom, left:right]
	io.imsave("cropped.jpg", crop)

	face_rect = biggest_face
	# Draw a box around each face we found
	win.add_overlay(face_rect)

	# Get the the face's pose
	pose_landmarks = face_pose_predictor(image, face_rect)

	# Draw the face landmarks on the screen.
	win.add_overlay(pose_landmarks)

dlib.hit_enter_to_continue()
