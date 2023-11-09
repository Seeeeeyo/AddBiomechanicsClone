from addbiomechanics.commands.abtract_command import AbstractCommand
import argparse
from addbiomechanics.auth import AuthContext
import os
import tempfile
from typing import List, Dict, Tuple
import itertools
import json


class PostProcessCommand(AbstractCommand):
    def register_subcommand(self, subparsers: argparse._SubParsersAction):
        parser = subparsers.add_parser(
            'post-process', help='This command will read a SubjectOnDisk binary file, or a folder full of them, '
                                 'do some processing (e.g. lowpass filter the values and/or standardize the sample '
                                 'rates), and then write out the result to a new binary file or folder with the '
                                 'same relative paths.')
        parser.add_argument('input_path', type=str)
        parser.add_argument('output_path', type=str)
        parser.add_argument('--geometry-folder', type=str, default=None)
        parser.add_argument(
            '--only-reviewed',
            help='Filter to only trial segments with reviews',
            type=bool,
            default=False)
        parser.add_argument(
            '--only-dynamics',
            help='Filter to only trial segments with dynamics',
            type=bool,
            default=False)
        parser.add_argument('--clean-up-noise', help='Smooth the finite-differenced quantities to have a similar frequency profile to the original signals. Also clean up CoP data to only include physically plausible CoPs (near the feet).', type=bool, default=False)
        parser.add_argument(
            '--recompute-values',
            help='Load skeletons and recompute all values, which will fill any new fields in B3D that have been added '
                 'since the original files were generated',
            type=bool,
            default=False)
        parser.add_argument(
            '--root-history-len',
            help='The number of frames to use when recomputing the root position and rotation history, in the root '
                 'frame. This is ignored unless --recompute-values is specified.',
            type=int,
            default=5
        )
        parser.add_argument(
            '--root-history-stride',
            help='The stride to use when recomputing the root position and rotation history, in the root '
                 'frame. This is ignored unless --recompute-values is specified.',
            type=int,
            default=1
        )
        parser.add_argument(
            '--sample-rate',
            help='The new sample rate to enforce on all the data, if specified, either by up-sampling or down-sampling',
            type=int,
            default=None)

    def run_local(self, args: argparse.Namespace) -> bool:
        if args.command != 'post-process':
            return False

        try:
            import nimblephysics as nimble
        except ImportError:
            print(
                "The required library 'nimblephysics' is not installed. Please install it and try this command again.")
            return True
        try:
            import numpy as np
        except ImportError:
            print("The required library 'numpy' is not installed. Please install it and try this command again.")
            return True
        try:
            from scipy.signal import butter, filtfilt, resample_poly, welch
            from scipy.interpolate import interp1d
        except ImportError:
            print("The required library 'scipy' is not installed. Please install it and try this command again.")
            return True

        # Handy little utility for resampling a discrete signal
        def resample_discrete(signal, old_rate, new_rate):
            # Compute the ratio of the old and new rates
            ratio = old_rate / new_rate
            # Use numpy's round and int functions to get the indices of the nearest values
            indices = (np.round(np.arange(0, len(signal), ratio))).astype(int)
            # Limit indices to the valid range
            indices = np.clip(indices, 0, len(signal) - 1)
            # Use advanced indexing to get the corresponding values
            resampled_signal = np.array(signal)[indices]
            return resampled_signal.tolist()

        input_path_raw: str = os.path.abspath(args.input_path)
        output_path_raw: str = os.path.abspath(args.output_path)
        sample_rate: int = args.sample_rate
        recompute_values: bool = args.recompute_values
        only_dynamics: bool = args.only_dynamics
        root_history_len: int = args.root_history_len
        root_history_stride: int = args.root_history_stride
        geometry_folder: str = args.geometry_folder
        clean_up_noise: bool = args.clean_up_noise
        if geometry_folder is not None:
            geometry_folder = os.path.abspath(geometry_folder) + '/'
        else:
            geometry_folder = os.path.abspath(os.path.join(os.path.dirname(input_path_raw), 'Geometry')) + '/'
        print('Geometry folder: ' + geometry_folder)

        input_output_pairs: List[Tuple[str, str]] = []

        if os.path.isfile(input_path_raw):
            input_output_pairs.append((input_path_raw, output_path_raw))
        elif os.path.isdir(input_path_raw):
            # Iterate over the directory structure, and append (input_path, output_path) pairs to
            # input_output_pairs for every file in the input_path_raw directory that ends with a *.bin.
            # Output_path preserves the relative path to the file, but is in the output_path_raw directory instead.
            for dirpath, dirnames, filenames in os.walk(input_path_raw):
                for filename in filenames:
                    if filename.endswith('.b3d'):
                        input_path = os.path.join(dirpath, filename)
                        # Create the output_path preserving the relative path
                        relative_path = os.path.relpath(input_path, input_path_raw)
                        output_path = os.path.join(output_path_raw, relative_path)
                        if os.path.exists(output_path):
                            print('Skipping ' + input_path + ' because the output file already exists at ' + output_path)
                        else:
                            # Ensure the directory structure for the output path exists
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)

                            input_output_pairs.append((input_path, output_path))

        print('Will post-process '+str(len(input_output_pairs))+' file' + ("s" if len(input_output_pairs) > 1 else ""))
        for file_index, (input_path, output_path) in enumerate(input_output_pairs):
            print('Reading SubjectOnDisk '+str(file_index+1)+'/'+str(len(input_output_pairs))+' at ' + input_path + '...')

            # Read all the contents from the current SubjectOnDisk
            subject: nimble.biomechanics.SubjectOnDisk = nimble.biomechanics.SubjectOnDisk(input_path)

            drop_trials: List[int] = []
            if only_dynamics:
                has_dynamics_pass = False
                for pass_num in range(subject.getNumProcessingPasses()):
                    if subject.getProcessingPassType(pass_num) == nimble.biomechanics.ProcessingPassType.DYNAMICS:
                        has_dynamics_pass = True
                        break
                if not has_dynamics_pass:
                    print('Skipping ' + input_path + ' because it does not have any dynamics processing passes.')
                    continue

                for trial in range(subject.getNumTrials()):
                    has_dynamics_pass = False
                    for pass_num in range(subject.getTrialNumProcessingPasses(trial)):
                        if subject.getProcessingPassType(pass_num) == nimble.biomechanics.ProcessingPassType.DYNAMICS:
                            has_dynamics_pass = True
                            break
                    if not has_dynamics_pass:
                        drop_trials.append(trial)

            print('Reading all frames')
            subject.loadAllFrames()

            trial_folder_path = os.path.join(os.path.dirname(input_path), 'trials')
            if os.path.exists(trial_folder_path) and os.path.isdir(trial_folder_path):
                trial_protos = subject.getHeaderProto().getTrials()
                for trial_index in range(subject.getNumTrials()):
                    original_name = trial_protos[trial_index].getOriginalTrialName()
                    split_index = trial_protos[trial_index].getSplitIndex()
                    review_path = os.path.join(trial_folder_path, original_name, 'segment_'+str(split_index+1), 'review.json')
                    missing_grf_reason: List[nimble.biomechanics.MissingGRFReason] = trial_protos[
                        trial_index].getMissingGRFReason()
                    user_reviewed = False
                    if os.path.exists(review_path):
                        review_json = json.load(open(review_path, 'r'))
                        missing_flags: List[bool] = review_json['missing_grf_data']
                        # There was a bug in the old UI which would add extra boolean onto the end of the
                        # missing_grf_data file. These are harmless, and we should just ignore them.
                        if len(missing_flags) >= len(missing_grf_reason):
                            for i in range(len(missing_grf_reason)):
                                if missing_flags[i]:
                                    missing_grf_reason[i] = nimble.biomechanics.MissingGRFReason.manualReview
                                else:
                                    # TODO: is this a good idea? This data will not have correct torques, angular
                                    #  residuals, etc.
                                    # missing_grf_reason[i] = nimble.biomechanics.MissingGRFReason.notMissingGRF
                                    pass
                            user_reviewed = True
                            print('User reviews incorporated from ' + review_path)
                        else:
                            print(f'Warning! Review file {review_path} has a smaller number of missing GRF flags ({len(missing_flags)}) than the B3D file ({len(missing_grf_reason)}). Skipping review file.')
                    if not user_reviewed:
                        missing_grf_reason = [
                            nimble.biomechanics.MissingGRFReason.manualReview for _ in range(len(missing_grf_reason))
                        ]
                    trial_protos[trial_index].setMissingGRFReason(missing_grf_reason)

            resampled = False
            if sample_rate is not None:
                print('Re-sampling kinematics + kinetics data at {} Hz...'.format(sample_rate))
                print('Warning! Re-sampling input source data (markers, IMU, EMG) is not yet supported, so those will '
                      'be zeroed out')
                resampled = True

                trial_protos = subject.getHeaderProto().getTrials()
                for trial in range(subject.getNumTrials()):
                    # Set the timestep
                    original_sample_rate = int(1.0 / subject.getTrialTimestep(trial))
                    if original_sample_rate != int(sample_rate):
                        trial_protos[trial].setTimestep(1.0 / sample_rate)

                        raw_force_plates: List[nimble.biomechanics.ForcePlate] = trial_protos[trial].getForcePlates()
                        for force_plate in raw_force_plates:
                            resampling_matrix, ground_heights = force_plate.getResamplingMatrixAndGroundHeights()
                            resampling_matrix = resample_poly(resampling_matrix, sample_rate, original_sample_rate, axis=1)
                            ground_heights = resample_discrete(ground_heights, original_sample_rate, sample_rate)
                            force_plate.setResamplingMatrixAndGroundHeights(resampling_matrix, ground_heights)
                        trial_protos[trial].setForcePlates(raw_force_plates)

                        trial_pass_protos = trial_protos[trial].getPasses()
                        trial_len = subject.getTrialLength(trial)
                        for processing_pass in range(subject.getTrialNumProcessingPasses(trial)):
                            resampling_matrix = trial_pass_protos[processing_pass].getResamplingMatrix()
                            resampling_matrix = resample_poly(resampling_matrix, sample_rate, original_sample_rate, axis=1)
                            trial_pass_protos[processing_pass].setResamplingMatrix(resampling_matrix)
                            trial_len = resampling_matrix.shape[1]
                        trial_protos[trial].setMarkerObservations([{}] * trial_len)

            if clean_up_noise or recompute_values or resampled:
                pass_skels: List[nimble.dynamics.Skeleton] = []
                for processing_pass in range(subject.getNumProcessingPasses()):
                    print('Reading skeleton for processing pass ' + str(processing_pass) + '...')
                    skel = subject.readSkel(processing_pass, geometryFolder=geometry_folder)
                    print('Pass type: ' + str(subject.getProcessingPassType(processing_pass)))
                    pass_skels.append(skel)

                for i in range(len(pass_skels)):
                    if pass_skels[i] is None and i > 0:
                        subject.getHeaderProto().getProcessingPasses()[i].setOpenSimFileText(
                            subject.getHeaderProto().getProcessingPasses()[i - 1].getOpenSimFileText())
                        pass_skels[i] = pass_skels[i - 1]

            if clean_up_noise:
                print('Cleaning up data')

                def find_cutoff_frequency(signal, fs=100) -> float:
                    frequencies, psd = welch(signal, fs, nperseg=min(1024, len(signal)))
                    cumulative_power = np.cumsum(psd)
                    total_power = np.sum(psd)
                    cutoff_power = 0.99 * total_power
                    cutoff_frequency_index = np.where(cumulative_power >= cutoff_power)[0][0]
                    return frequencies[cutoff_frequency_index]

                trial_protos = subject.getHeaderProto().getTrials()
                new_overall_pass = subject.getHeaderProto().addProcessingPass()
                new_overall_pass.setProcessingPassType(nimble.biomechanics.ProcessingPassType.LOW_PASS_FILTER)
                new_overall_pass.setOpenSimFileText(subject.getHeaderProto().getProcessingPasses()[-2].getOpenSimFileText())
                pass_skels.append(pass_skels[-1])

                for trial in range(subject.getNumTrials()):
                    if trial in drop_trials:
                        continue
                    # Add a lowpass filter pass to the end of the trial
                    trial_pass_protos = trial_protos[trial].getPasses()
                    last_pass_proto = trial_pass_protos[-1]
                    poses = last_pass_proto.getPoses()

                    # Skip short trials, add them to the drop list
                    if poses.shape[1] <= 12:
                        drop_trials.append(trial)
                        continue

                    fs = int(1.0 / trial_protos[trial].getTimestep())
                    cutoff_frequencies: List[float] = [find_cutoff_frequency(poses[i, :], fs) for i in range(poses.shape[0])]
                    cutoff = max(max(cutoff_frequencies), 1.0)
                    print(f"Cutoff Frequency to preserve 99% of signal power: {cutoff} Hz")
                    nyq = 0.5 * fs
                    normal_cutoff = cutoff / nyq
                    if cutoff >= nyq:
                        print('Warning! Cutoff frequency is at or above Nyquist frequency. This suggests some funny business with the data. Dropping this trial to be on the safe side.')
                        drop_trials.append(trial)
                    else:
                        b, a = butter(3, normal_cutoff, btype='low', analog=False)
                        new_pass = trial_protos[trial].addPass()
                        new_pass.copyValuesFrom(last_pass_proto)
                        new_pass.setType(nimble.biomechanics.ProcessingPassType.LOW_PASS_FILTER)
                        new_pass.setLowpassFilterOrder(3)
                        new_pass.setLowpassCutoffFrequency(cutoff)
                        accs = new_pass.getAccs()
                        if accs.shape[1] > 1:
                            accs[:, 0] = accs[:, 1]
                            accs[:, -1] = accs[:, -2]
                            new_pass.setAccs(accs)
                        vels = new_pass.getVels()
                        if vels.shape[1] > 1:
                            vels[:, 0] = vels[:, 1]
                            vels[:, -1] = vels[:, -2]
                            new_pass.setVels(vels)
                        if poses.shape[1] > 12:
                            new_pass.setResamplingMatrix(filtfilt(b, a, new_pass.getResamplingMatrix(), axis=1))

                        # Copy force plate data to Python
                        raw_force_plates = trial_protos[trial].getForcePlates()
                        cops = [force_plate.centersOfPressure for force_plate in raw_force_plates]
                        forces = [force_plate.forces for force_plate in raw_force_plates]

                        print('Fixing COM acceleration for trial ' + str(trial))
                        skel = pass_skels[-1]
                        new_poses = new_pass.getPoses()
                        new_vels = new_pass.getVels()
                        new_accs = new_pass.getAccs()
                        for t in range(new_poses.shape[1]):
                            pass_skels[-1].setPositions(new_poses[:, t])
                            pass_skels[-1].setVelocities(new_vels[:, t])
                            pass_skels[-1].setAccelerations(new_accs[:, t])
                            com_acc = pass_skels[-1].getCOMLinearAcceleration() - pass_skels[-1].getGravity()
                            total_acc = np.sum(np.row_stack([forces[f][t] for f in range(len(raw_force_plates))]), axis=0) / pass_skels[-1].getMass()
                            # print('Expected acc: '+str(total_acc))
                            # print('Got acc: '+str(com_acc))
                            root_acc_correction = total_acc - com_acc
                            # print('Correcting root acc: '+str(root_acc_correction))
                            new_accs[3:6, t] += root_acc_correction
                        trial_protos[trial].getPasses()[-1].setAccs(new_accs)


                        # Check the CoP data to ensure it is physically plausible
                        print('Cleaning up CoP data for trial ' + str(trial))
                        foot_bodies = [skel.getBodyNode(name) for name in subject.getGroundForceBodies()]
                        dist_threshold_m = 0.35  # A bit more than 1 foot

                        for t in range(new_poses.shape[1]):
                            skel.setPositions(new_poses[:, t])
                            foot_body_locations = [body.getWorldTransform().translation() for body in foot_bodies]
                            for f in range(len(raw_force_plates)):
                                force = forces[f][t]
                                if np.linalg.norm(force) > 1e-3:
                                    cop = cops[f][t]
                                    dist_to_feet = [np.linalg.norm(cop - foot_body_location) for foot_body_location in foot_body_locations]
                                    if min(dist_to_feet) > dist_threshold_m:
                                        closest_foot = np.argmin(dist_to_feet)
                                        # print(f"Warning! CoP for plate {f} is not near a foot at time {t}. Bringing it within {dist_threshold_m}m of the closest foot.")
                                        # print(f"  Force: {force}")
                                        # print(f"  CoP: {cop}")
                                        # print(f"  Dist to feet: {dist_to_feet}")
                                        cop = foot_body_locations[closest_foot] + dist_threshold_m * (cop - foot_body_locations[closest_foot]) / np.linalg.norm(cop - foot_body_locations[closest_foot])
                                        cops[f][t] = cop
                        for f in range(len(raw_force_plates)):
                            raw_force_plates[f].centersOfPressure = cops[f]

            if recompute_values or resampled or clean_up_noise:
                print('Recomputing values in the raw B3D')

                subject.getHeaderProto().setNumJoints(pass_skels[0].getNumJoints())

                trial_protos = subject.getHeaderProto().getTrials()
                for trial in range(subject.getNumTrials()):
                    timestep = subject.getTrialTimestep(trial)
                    raw_force_plates = trial_protos[trial].getForcePlates()
                    # Re-sample the discrete values
                    trial_protos[trial].setMissingGRFReason(resample_discrete(trial_protos[trial].getMissingGRFReason(),
                                                                    original_sample_rate,
                                                                    sample_rate))
                    trial_pass_protos = trial_protos[trial].getPasses()
                    print('##########')
                    print('Trial '+str(trial)+':')
                    for processing_pass in range(subject.getTrialNumProcessingPasses(trial)):
                        explicit_vel = np.copy(trial_pass_protos[processing_pass].getVels())
                        explicit_acc = np.copy(trial_pass_protos[processing_pass].getAccs())
                        trial_pass_protos[processing_pass].computeValuesFromForcePlates(pass_skels[processing_pass], timestep, trial_pass_protos[processing_pass].getPoses(), subject.getGroundForceBodies(), raw_force_plates, rootHistoryLen=root_history_len, rootHistoryStride=root_history_stride, explicitVels=explicit_vel, explicitAccs=explicit_acc)
                        assert(np.all(trial_pass_protos[processing_pass].getAccs() == explicit_acc))
                        assert(np.all(trial_pass_protos[processing_pass].getVels() == explicit_vel))
                        print('Pass '+str(processing_pass)+' of ' + str(subject.getTrialNumProcessingPasses(trial)) +' type: '+str(subject.getProcessingPassType(processing_pass)))
                        print('Range on joint accelerations: '+str(np.min(trial_pass_protos[processing_pass].getAccs()))+' to '+str(np.max(trial_pass_protos[processing_pass].getAccs())))
                        print('Range on joint torques: '+str(np.min(trial_pass_protos[processing_pass].getTaus()))+' to '+str(np.max(trial_pass_protos[processing_pass].getTaus())))
                        print('Linear Residuals: '+str(np.mean(trial_pass_protos[processing_pass].getLinearResidual())))
                        print('Angular Residuals: '+str(np.mean(trial_pass_protos[processing_pass].getAngularResidual())))

            if len(drop_trials) > 0:
                print('Dropping trials: '+str(drop_trials))
                filtered_trials = [trial for i, trial in enumerate(subject.getHeaderProto().getTrials()) if i not in drop_trials]
                subject.getHeaderProto().setTrials(filtered_trials)

            # os.path.dirname gets the directory portion from the full path
            directory = os.path.dirname(output_path)
            # Create the directory structure, if it doesn't exist already
            os.makedirs(directory, exist_ok=True)
            # Now write the output back out to the new SubjectOnDisk file
            print('Writing SubjectOnDisk to {}...'.format(output_path))
            nimble.biomechanics.SubjectOnDisk.writeB3D(output_path, subject.getHeaderProto())
            print('Done '+str(file_index+1)+'/'+str(len(input_output_pairs)))

        print('Post-processing finished!')

        return True
