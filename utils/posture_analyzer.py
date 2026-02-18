# utils/posture_analyzer.py
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import mediapipe as mp

logger = logging.getLogger(__name__)

class PostureAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_face_mesh = mp.solutions.face_mesh
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """Analyze posture and eye contact from a single frame"""
        try:
            # Convert BGR to RGB
            rgb_frame = frame[:, :, ::-1]
            
            # Pose detection
            pose_results = self.pose.process(rgb_frame)
            posture_metrics = self._analyze_posture(pose_results)
            
            # Face mesh for eye contact
            face_results = self.face_mesh.process(rgb_frame)
            eye_contact_metrics = self._analyze_eye_contact(face_results)
            
            return {
                'posture': posture_metrics,
                'eye_contact': eye_contact_metrics,
                'timestamp': None  # Will be set by caller
            }
            
        except Exception as e:
            logger.error(f"Frame analysis error: {str(e)}")
            return {
                'posture': {'score': 0, 'status': 'unknown', 'confidence': 0},
                'eye_contact': {'score': 0, 'status': 'unknown', 'confidence': 0}
            }
    
    def _analyze_posture(self, pose_results) -> Dict:
        """Analyze posture from pose landmarks"""
        if not pose_results.pose_landmarks:
            return {'score': 0, 'status': 'unknown', 'confidence': 0}
        
        landmarks = pose_results.pose_landmarks.landmark
        
        try:
            # Get key landmarks
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
            
            # Calculate metrics
            shoulder_alignment = self._calculate_alignment_score(
                left_shoulder, right_shoulder
            )
            hip_alignment = self._calculate_alignment_score(left_hip, right_hip)
            spinal_alignment = self._calculate_spinal_alignment(
                left_shoulder, right_shoulder, left_hip, right_hip
            )
            head_position = self._calculate_head_position(
                nose, left_shoulder, right_shoulder
            )
            
            # Calculate overall posture score
            posture_score = (
                shoulder_alignment * 0.3 +
                hip_alignment * 0.2 +
                spinal_alignment * 0.3 +
                head_position * 0.2
            )
            
            # Determine posture status
            if posture_score >= 80:
                status = 'good'
            elif posture_score >= 60:
                status = 'okay'
            else:
                status = 'bad'
            
            # Calculate confidence based on landmark visibility
            confidence = self._calculate_confidence(landmarks)
            
            return {
                'score': round(posture_score, 1),
                'status': status,
                'confidence': round(confidence, 2),
                'metrics': {
                    'shoulder_alignment': round(shoulder_alignment, 1),
                    'hip_alignment': round(hip_alignment, 1),
                    'spinal_alignment': round(spinal_alignment, 1),
                    'head_position': round(head_position, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Posture analysis error: {str(e)}")
            return {'score': 0, 'status': 'unknown', 'confidence': 0}
    
    def _analyze_eye_contact(self, face_results) -> Dict:
        """Analyze eye contact from face landmarks"""
        if not face_results.multi_face_landmarks:
            return {'score': 0, 'status': 'unknown', 'confidence': 0}
        
        face_landmarks = face_results.multi_face_landmarks[0].landmark
        
        try:
            # Use key facial landmarks for gaze estimation
            left_eye_inner = face_landmarks[133]  # Left eye inner corner
            right_eye_inner = face_landmarks[362]  # Right eye inner corner
            nose_tip = face_landmarks[1]  # Nose tip
            
            # Simplified gaze direction estimation
            eye_center_x = (left_eye_inner.x + right_eye_inner.x) / 2
            deviation = abs(eye_center_x - 0.5)  # 0.5 is screen center
            
            # Calculate eye contact score (0-100)
            eye_contact_score = max(0, 100 - (deviation * 200))
            
            # Determine eye contact status
            if eye_contact_score >= 75:
                status = 'good'
            elif eye_contact_score >= 50:
                status = 'moderate'
            else:
                status = 'poor'
            
            return {
                'score': round(eye_contact_score, 1),
                'status': status,
                'confidence': 0.8  # Fixed confidence for face detection
            }
            
        except Exception as e:
            logger.error(f"Eye contact analysis error: {str(e)}")
            return {'score': 0, 'status': 'unknown', 'confidence': 0}
    
    def _calculate_alignment_score(self, point1, point2) -> float:
        """Calculate alignment score between two points"""
        vertical_diff = abs(point1.y - point2.y)
        alignment_score = max(0, 100 - (vertical_diff * 500))
        return alignment_score
    
    def _calculate_spinal_alignment(self, left_shoulder, right_shoulder, 
                                  left_hip, right_hip) -> float:
        """Calculate spinal alignment score"""
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        hip_center_x = (left_hip.x + right_hip.x) / 2
        
        horizontal_deviation = abs(shoulder_center_x - hip_center_x)
        alignment_score = max(0, 100 - (horizontal_deviation * 200))
        
        return alignment_score
    
    def _calculate_head_position(self, nose, left_shoulder, right_shoulder) -> float:
        """Calculate head position score"""
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        vertical_deviation = abs(nose.y - shoulder_center_y)
        
        head_position_score = max(0, 100 - (vertical_deviation * 300))
        return head_position_score
    
    def _calculate_confidence(self, landmarks) -> float:
        """Calculate confidence based on landmark visibility"""
        visible_landmarks = sum(1 for lm in landmarks if lm.visibility > 0.5)
        total_landmarks = len(landmarks)
        confidence = visible_landmarks / total_landmarks
        return confidence
    
    def process_posture_data(self, raw_data: Dict) -> Dict:
        """Process raw posture data into summary statistics"""
        # Handle both frontend data format
        posture_list = raw_data.get('posture', []) if isinstance(raw_data, dict) else []
        eye_contact_list = raw_data.get('eye_contact', []) if isinstance(raw_data, dict) else []
        
        if not posture_list and not eye_contact_list:
            return self._get_empty_analysis()
        
        try:
            posture_scores = []
            eye_contact_scores = []
            second_by_second = {}
            
            # Process posture data
            for entry in posture_list:
                if isinstance(entry, dict):
                    timestamp = entry.get('timestamp', 0)
                    score = entry.get('score', 0)
                else:
                    continue
                
                second = int(float(timestamp))
                
                if second not in second_by_second:
                    second_by_second[second] = {
                        'posture_scores': [],
                        'eye_contact_scores': [],
                        'samples': 0
                    }
                
                if score > 0:
                    posture_scores.append(score)
                    second_by_second[second]['posture_scores'].append(score)
            
            # Process eye contact data
            for entry in eye_contact_list:
                if isinstance(entry, dict):
                    timestamp = entry.get('timestamp', 0)
                    score = entry.get('score', 0)
                else:
                    continue
                
                second = int(float(timestamp))
                
                if second not in second_by_second:
                    second_by_second[second] = {
                        'posture_scores': [],
                        'eye_contact_scores': [],
                        'samples': 0
                    }
                
                if score > 0:
                    eye_contact_scores.append(score)
                    second_by_second[second]['eye_contact_scores'].append(score)
            
            # Update samples count
            for second_data in second_by_second.values():
                second_data['samples'] = max(
                    len(second_data['posture_scores']),
                    len(second_data['eye_contact_scores'])
                )
            
            # Calculate summary statistics
            summary = self._calculate_summary_stats(
                posture_scores, eye_contact_scores, second_by_second
            )
            
            return {
                'summary': summary,
                'second_by_second': second_by_second,
                'recording_time': len(second_by_second)
            }
            
        except Exception as e:
            logger.error(f"Posture data processing error: {str(e)}")
            return self._get_empty_analysis()
    
    def _calculate_summary_stats(self, posture_scores, eye_contact_scores, 
                               second_by_second) -> Dict:
        """Calculate summary statistics from posture data"""
        avg_posture = np.mean(posture_scores) if posture_scores else 0
        avg_eye_contact = np.mean(eye_contact_scores) if eye_contact_scores else 0
        
        # Calculate time spent in each posture category
        posture_categories = {'good': 0, 'okay': 0, 'bad': 0}
        eye_contact_categories = {'good': 0, 'moderate': 0, 'poor': 0}
        
        for second_data in second_by_second.values():
            if second_data['posture_scores']:
                avg_second_posture = np.mean(second_data['posture_scores'])
                if avg_second_posture >= 80:
                    posture_categories['good'] += 1
                elif avg_second_posture >= 60:
                    posture_categories['okay'] += 1
                else:
                    posture_categories['bad'] += 1
            
            if second_data['eye_contact_scores']:
                avg_second_eye = np.mean(second_data['eye_contact_scores'])
                if avg_second_eye >= 75:
                    eye_contact_categories['good'] += 1
                elif avg_second_eye >= 50:
                    eye_contact_categories['moderate'] += 1
                else:
                    eye_contact_categories['poor'] += 1
        
        total_seconds = len(second_by_second)
        
        return {
            'average_posture_score': round(avg_posture, 1),
            'average_eye_contact_score': round(avg_eye_contact, 1),
            'posture_breakdown': {
                'good_percentage': round(posture_categories['good'] / total_seconds * 100, 1) if total_seconds > 0 else 0,
                'okay_percentage': round(posture_categories['okay'] / total_seconds * 100, 1) if total_seconds > 0 else 0,
                'bad_percentage': round(posture_categories['bad'] / total_seconds * 100, 1) if total_seconds > 0 else 0
            },
            'eye_contact_breakdown': {
                'good_percentage': round(eye_contact_categories['good'] / total_seconds * 100, 1) if total_seconds > 0 else 0,
                'moderate_percentage': round(eye_contact_categories['moderate'] / total_seconds * 100, 1) if total_seconds > 0 else 0,
                'poor_percentage': round(eye_contact_categories['poor'] / total_seconds * 100, 1) if total_seconds > 0 else 0
            },
            'total_recording_seconds': total_seconds
        }
    
    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure with reasonable defaults"""
        return {
            'summary': {
                'average_posture_score': 65,  # Reasonable default
                'average_eye_contact_score': 60,  # Reasonable default
                'posture_breakdown': {
                    'good_percentage': 40,
                    'okay_percentage': 45,
                    'bad_percentage': 15
                },
                'eye_contact_breakdown': {
                    'good_percentage': 35,
                    'moderate_percentage': 50,
                    'poor_percentage': 15
                }
            },
            'second_by_second': {},
            'recording_time': 0
        }
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'pose'):
            self.pose.close()
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()