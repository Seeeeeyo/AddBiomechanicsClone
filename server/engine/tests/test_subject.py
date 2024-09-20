import shutil
import unittest
from subject import Subject
from trial import TrialSegment, Trial
from typing import Dict, List, Any
import os
import nimblephysics as nimble
from inspect import getsourcefile

TESTS_PATH = os.path.dirname(getsourcefile(lambda:0))
DATA_PATH = os.path.join(TESTS_PATH, '..', '..', 'data')
TEST_DATA_PATH = os.path.join(TESTS_PATH, '..', 'test_data')

def reset_test_data(name: str):
    original_path = os.path.join(TEST_DATA_PATH, f'{name}_original')
    live_path = os.path.join(TEST_DATA_PATH, name)
    if os.path.exists(live_path):
        shutil.rmtree(live_path)
    shutil.copytree(original_path, live_path)


class TestSubject(unittest.TestCase):
    def test_parse_json(self):
        subject = Subject()
        json_blob: Dict[str, Any] = {}
        json_blob['massKg'] = 42.0
        json_blob['heightM'] = 2.0
        subject.parse_subject_json(json_blob)
        self.assertEqual(42.0, subject.massKg)
        self.assertEqual(2.0, subject.heightM)

    def test_load_subject_json(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_subject_json(os.path.join(TEST_DATA_PATH, 'opencap_test', '_subject.json'))

    def test_load_subject(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.skeletonPreset = 'custom'
        subject.load_model_files(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        self.assertIsNotNone(subject.customOsim)
        self.assertIsNotNone(subject.skeleton)
        self.assertIsNotNone(subject.markerSet)
        has_custom_joint = False
        for i in range(subject.skeleton.getNumJoints()):
            joint = subject.skeleton.getJoint(i)
            if nimble.dynamics.CustomJoint1.getStaticType() == joint.getType() or nimble.dynamics.CustomJoint2.getStaticType() == joint.getType():
                has_custom_joint = True
        self.assertTrue(has_custom_joint)

    def test_load_subject_simplified(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.skeletonPreset = 'custom'
        # If we trigger to export either an SDF or an MJCF, we use simplified joint definitions, so we run a
        # pre-processing step on the data.
        subject.exportSDF = True
        subject.load_model_files(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        self.assertIsNotNone(subject.customOsim)
        self.assertIsNotNone(subject.skeleton)
        self.assertIsNotNone(subject.markerSet)
        for i in range(subject.skeleton.getNumJoints()):
            joint = subject.skeleton.getJoint(i)
            self.assertNotEqual(nimble.dynamics.CustomJoint1.getStaticType(), joint.getType())
            self.assertNotEqual(nimble.dynamics.CustomJoint2.getStaticType(), joint.getType())

    def test_load_trial(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_trials(os.path.join(TEST_DATA_PATH, 'opencap_test', 'trials'))
        self.assertEqual(4, len(subject.trials))

    def test_load_folder(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_folder(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        self.assertIsNotNone(subject.customOsim)
        self.assertIsNotNone(subject.skeleton)
        self.assertIsNotNone(subject.markerSet)
        self.assertEqual(4, len(subject.trials))

    def test_segment_trials(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_folder(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        subject.segment_trials()
        for trial in subject.trials:
            for segment in trial.segments:
                for force_plate in segment.force_plates:
                    self.assertGreater(len(segment.original_marker_observations), 0)
                    self.assertEqual(len(segment.original_marker_observations), len(force_plate.forces))
                    self.assertEqual(len(segment.original_marker_observations), len(force_plate.moments))
                    self.assertEqual(len(segment.original_marker_observations), len(force_plate.centersOfPressure))

    def test_rescale_osim_model(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_folder(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        subject.kinematics_skeleton = subject.skeleton
        print(os.path.join(TEST_DATA_PATH, 'opencap_test', 'unscaled_generic.osim'))
        self.assertTrue(os.path.exists(os.path.join(TEST_DATA_PATH, 'opencap_test', 'unscaled_generic.osim')))
        subject.scale_osim(os.path.join(TEST_DATA_PATH, 'opencap_test', 'unscaled_generic.osim'), os.path.join(TEST_DATA_PATH, 'opencap_test', 'scaled_test.osim'), subject.skeleton, subject.markerSet)
        self.assertTrue(os.path.exists(os.path.join(TEST_DATA_PATH, 'opencap_test', 'scaled_test.osim')))

    def test_write_opensim_results_without_data(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_folder(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        subject.segment_trials()
        subject.kinematics_skeleton = subject.skeleton
        subject.write_opensim_results(os.path.join(TEST_DATA_PATH, 'opencap_test', 'osim_results'), DATA_PATH)
        self.assertTrue(os.path.exists(os.path.join(TEST_DATA_PATH, 'opencap_test', 'osim_results', 'Models', 'match_markers_but_ignore_physics.osim')))

    def test_write_web_results_without_data(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_folder(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        subject.segment_trials()
        subject.write_web_results(os.path.join(TEST_DATA_PATH, 'opencap_test', 'web_results'))

    def test_kinematics_fit(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_folder(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        subject.segment_trials()
        subject.kinematicsIterations = 20
        subject.initialIKRestarts = 3
        subject.run_kinematics_fit(DATA_PATH)
        subject.write_opensim_results(os.path.join(TEST_DATA_PATH, 'opencap_test', 'osim_results'), DATA_PATH)
        self.assertTrue(os.path.exists(os.path.join(TEST_DATA_PATH, 'opencap_test', 'osim_results', 'Models', 'match_markers_but_ignore_physics.osim')))
        subject.write_b3d_file(os.path.join(TEST_DATA_PATH, 'opencap_test' 'subject.b3d'), os.path.join(TEST_DATA_PATH, 'opencap_test', 'osim_results'), 'http://addbiomechanics.org')
        subject.write_web_results(os.path.join(TEST_DATA_PATH, 'opencap_test'))

    def test_dynamics_fit(self):
        subject = Subject()
        reset_test_data('opencap_test')
        subject.load_folder(os.path.join(TEST_DATA_PATH, 'opencap_test'), DATA_PATH)
        subject.segment_trials()
        subject.kinematicsIterations = 20
        subject.initialIKRestarts = 3
        subject.run_kinematics_fit(DATA_PATH)
        subject.run_dynamics_fit()
        subject.write_opensim_results(os.path.join(TEST_DATA_PATH, 'opencap_test', 'osim_results'), DATA_PATH)
        subject.write_b3d_file(os.path.join(TEST_DATA_PATH, 'opencap_test', 'subject.b3d'), os.path.join(TEST_DATA_PATH, 'opencap_test', 'osim_results'), 'http://addbiomechanics.org')
        subject.write_web_results(os.path.join(TEST_DATA_PATH, 'opencap_test'))
