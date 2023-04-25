import React, { useState, useRef, useEffect } from "react";
import Select, { components, MultiValueGenericProps, ControlProps, MultiValue, Props } from 'react-select';
import './TagEditor.scss';

type Option = {
  value: string,
  label: string,
  addedNumberUnits?: string,
  min?: number,
  max?: number,
  integer?: boolean,
  children?: Option[],
  level?: number,
  isHeader?: boolean,
  isNonSelectable?: true
}

const subjectOptions: Option[] = [
  { value: 'demographics', label: 'Demographics', isHeader:true, isNonSelectable: true, children: [
     { value: 'age', label: 'Age', addedNumberUnits: 'years', min: 10, max: 90, integer: true },
  ]},
  { value: 'phenotypes', label: 'Phenotypes', isHeader:true, isNonSelectable: true, children: [
     { value: 'healthy', label: 'Unimpaired' },
     { value: 'parkinsons', label: 'Parkinsons', isHeader:true, children: [
        { value: 'freezing_of_gait', label: 'Freezing of Gait' },
        { value: 'tremor', label: 'Tremor' },
        { value: 'rigidity', label: 'Rigidity' },
        { value: 'bradykinesia', label: 'Bradykinesia' },
     ]},
     { value: 'muscular_distrophy', label: 'Muscular Dystrophy' },
     { value: 'cerebral_palsy', label: 'Cerebral Palsy' },
     { value: 'spina_bifida', label: 'Spina Bifida' },
     { value: 'stroke', label: 'Stroke', isHeader:true, children: [
        { value: 'stroke_left_hemiparesis', label: 'Stroke Left Hemiparesis' },
        { value: 'stroke_right_hemiparesis', label: 'Stroke Right Hemiparesis' },
     ]},
     { value: 'multiple_sclerosis', label: 'multiple sclerosis' },
     { value: 'dystonia', label: 'Dystonia' },
     { value: 'alzheimers', label: 'Alzheimers' },
     { value: 'chronic_pain', label: 'chronic pain' },
     { value: 'traumatic_brain_injury', label: 'traumatic brain injury' },
     { value: 'ptsd', label: 'ptsd' },
     { value: 'tbi', label: 'Traumatic Brain Injury (TBI)' },
     { value: 'concussion', label: 'Concussion' },
     { value: 'cognitive_impairment', label: 'Cognitive Impairment' },
     { value: 'dementia', label: 'Dementia' },
     { value: 'osteoarthritis', label: 'Osteoarthritis', isHeader:true, children: [
        { value: 'knee_osteoarthritis_right', label: 'Knee Osteoarthritis - Right' },
        { value: 'knee_osteoarthritis_left', label: 'Knee Osteoarthritis - Left' },
     ]},
     { value: 'pregnant', label: 'Pregnant' },
     { value: 'post_partum', label: 'Postpartum' },
     { value: 'blind', label: 'Blind' },
     { value: 'visually_impaired', label: 'Visually Impaired' },
     { value: 'limb_loss_amputation', label: 'Limb Loss/Amputation', isHeader:true, children: [
        { value: 'trans_femoral_amputation_left', label: 'Trans-femoral Amputation - Left' },
        { value: 'trans_femoral_amputation_right', label: 'Trans-femoral Amputation - Right' },
        { value: 'trans_tibial_amputation_left', label: 'Trans-tibial Amputation - Left' },
        { value: 'trans_tibial_amputation_right', label: 'Trans-tibial Amputation - Right' },
        { value: 'trans_radial_amputation_left', label: 'Trans-radial Amputation - Left' },
        { value: 'trans_radial_amputation_right', label: 'Trans-radial Amputation - Right' },
        { value: 'trans_humeral_amputation_left', label: 'Trans-humeral Amputation - Left' },
        { value: 'trans_humeral_amputation_right', label: 'Trans-humeral Amputation - Right' },
     ]},
     { value: 'athlete', label: 'Athlete' },
  ]},
];

const trialOptions: Option[] = [
  { value: 'movement_types', label: 'Movement Types', isHeader:true, isNonSelectable: true, children: [
     { value: 'running', label: 'Running' },
     { value: 'walking', label: 'Walking' },
     { value: 'sit_to_stand', label: 'Sit to Stand' },
     { value: 'jump', label: 'Jumping' },
     { value: 'stair_climbing', label: 'Stairs - Climbing' },
     { value: 'stair_descending', label: 'Stairs - Descending' },
     { value: 'biking', label: 'Biking' },
     { value: 'dance', label: 'Dancing' },
     { value: 'loaded_walking', label: 'Loaded Walking', addedNumberUnits: 'kg' },
     { value: 'crawling', label: 'Crawling' },
     { value: 'climbing', label: 'Climbing' },
     { value: 'squatting', label: 'Squatting' },
     { value: 'kneeling', label: 'Kneeling' },
     { value: 'sitting', label: 'Sitting' },
     { value: 'standing', label: 'Standing' },
     { value: 'cutting', label: 'Cutting' },
     { value: 'lifting', label: 'Lifting' },
     { value: 'swimming', label: 'Swimming' },
     { value: 'carrying_in_the_hands', label: 'Carrying in the hands' },
     { value: 'carrying_in_the_arms', label: 'Carrying in the arms' },
     { value: 'carrying_on_shoulders_hip_back', label: 'Carrying on Shoulders, Hips, and Back' },
     { value: 'putting_down_objects', label: 'Putting Down Objects' },
     { value: 'gait_initiation', label: 'Gait Initiation' },
     { value: 'reaching', label: 'Reaching' },
     { value: 'upper_extremity_movement', label: 'Upper Extremity Movement' },
     { value: 'pitching', label: 'Pitching' },
     { value: 'volleyball_hitting', label: 'Volleyball Hitting' },
     { value: 'sprinting', label: 'Sprinting' },
     { value: 'wheelchair_propulsion', label: 'Wheelchair Propulsion' },
  ]},
  { value: 'conditions_devices', label: 'Conditions - Devices', isHeader:true, isNonSelectable: true, children: [
     { value: 'exo_powered', label: 'Exo - Powered' },
     { value: 'exo_unpowered', label: 'Exo - Unpowered' },
     { value: 'exo_passive', label: 'Exo - Passive' },
     { value: 'prosthetic_powered', label: 'Prosthetic - Powered' },
     { value: 'prosthetic_passive', label: 'Prosthetic - Passive' },
     { value: 'rigid_brace_left_ankle', label: 'Brace (Rigid) - Left Ankle' },
     { value: 'rigid_brace_right_ankle', label: 'Brace (Rigid) - Right Ankle' },
     { value: 'rigid_brace_left_knee', label: 'Brace (Rigid) - Left Knee' },
     { value: 'rigid_brace_right_knee', label: 'Brace (Rigid) - Right Knee' },
     { value: 'rigid_brace_left_hip', label: 'Brace (Rigid) - Left Hip' },
     { value: 'rigid_brace_right_hip', label: 'Brace (Rigid) - Right Hip' },
     { value: 'pneumatic_jets_shoes', label: 'Pneumatic Jets (Shoes)' },
  ]},
  { value: 'conditions_experimental_conditions', label: 'Conditions - Experimental conditions', isHeader:true, isNonSelectable: true, children: [
     { value: 'movement_speed', label: 'Movement Speed', addedNumberUnits: 'm/s' },
     { value: 'treadmill_speed', label: 'Treadmill Speed', addedNumberUnits: 'm/s' },
     { value: 'treadmill_angle', label: 'Treadmill Angle', addedNumberUnits: 'deg' },
     { value: 'blindfolded', label: 'Blindfolded' },
     { value: 'balance_perturbation_impulse', label: 'Balance Perturbation Impulse', addedNumberUnits: 'N*s' },
     { value: 'balance_perturbation_angle', label: 'Balance Perturbation Angle', addedNumberUnits: 'deg' },
     { value: 'dual_task', label: 'Dual Task' },
     { value: 'biofeedback', label: 'Biofeedback' },
     { value: 'calibration', label: 'Calibration' },
     { value: 'arms_crossed', label: 'Arms Crossed' },
     { value: 'timed_up_and_go', label: 'Timed Up and Go (TUG)' },
     { value: 'six_minute_walk', label: '6MWT' },
     { value: 'walking_with_turns', label: 'Walking with Turns' },
  ]},
  { value: 'terrain', label: 'Terrain', isHeader:true, isNonSelectable: true, children: [
     { value: 'split_belt', label: 'Split-belt Treadmill' },
     { value: 'out_of_lab', label: 'Out of Lab' },
     { value: 'overground', label: 'Overground' },
     { value: 'treadmill', label: 'Treadmill' },
     { value: 'pitching_mound', label: 'Pitching Mound' },
     { value: 'sports_field', label: 'Sports Field' },
     { value: 'sports_track', label: 'Sports Track' },
     { value: 'sports_court', label: 'Sports Court' },
  ]},
];

const MultiValueLabel = (props: MultiValueGenericProps<Option>) => {
  let numberValues = (props.selectProps as any).numberValues;
  let hideNumbers = (props.selectProps as any).hideNumbers;
  const [value, setValue] = useState(props.data.value in numberValues ? numberValues[props.data.value] : 0.0);
  const inputRef = useRef(null as any as HTMLInputElement);

  useEffect(() => {
    setValue(numberValues[props.data.value]);
  }, [numberValues[props.data.value]])

  let numberInput = null;
  if (props.data.addedNumberUnits != null && !hideNumbers) {
    numberInput = <span>
      :<input className="TagEditor__number_input" type="number" ref={inputRef} onKeyDown={(e) => { e.stopPropagation(); }} onKeyPress={(e) => {
        e.stopPropagation();
        if (e.key === "Enter" && inputRef.current != null) {
          inputRef.current.blur();
        }
      }} value={value} onChange={(e) => {
        let rawValue = parseFloat(e.target.value);
        setValue(rawValue);
      }} onBlur={() => {
        const onChangeOption = (props.selectProps as any).onChangeOption;
        let rawValue = value;
        if (props.data.integer) {
          rawValue = Math.round(rawValue);
        }
        if ((props.data.min != null) && rawValue < props.data.min) {
          rawValue = props.data.min;
        }
        if ((props.data.max != null) && rawValue > props.data.max) {
          rawValue = props.data.max;
        }
        setValue(rawValue);
        onChangeOption(props.data, rawValue);
      }} />
      {props.data.addedNumberUnits}
    </span>;
  }

  return (
    <div className="TagEditor__tag">
      {props.children}
      {numberInput}
    </div>
  )
}

const getOptionLabel = (option:Option) => option.label;

const getOptionValue = (option:Option) => option.value;

const formatOptionLabel = ({ value, label, level, isHeader}: Option) => {
  const fontWeight = isHeader ? "bold" : "default";
  return (
    <span style={{ fontWeight }}>
      {label}
    </span>
  );
};

function flattenOptions(options: Option[], level: number = 0): Option[] {
  let result: Option[] = [];
  options.forEach((option) => {
    // add current option to result with its level
    result.push({ ...option, level });

    // recursively flatten children, incrementing level by 1
    if (option.children) {
      result = [...result, ...flattenOptions(option.children, level + 1)];
    }
  });
  return result;
}

const NoOptionsMessage = () => {
  const formURL = "https://docs.google.com/forms/d/e/1FAIpQLScqGhozFWp-33WoO8g9WGda3bf8cm2bvcDtIM1F7jAifwcIlw/viewform?usp=sf_link";

  return <div className="m-2">
    No tags match your search. We use structured tags, instead of free form text notes, to avoid accidentally hosting Personally Identifiable Information (PII) on the platform. If you don't find the tags you need, fill out <a href={formURL} target="_blank">this form</a> (opens in a new tab) to request new tags!
  </div>
}

type TagEditorProps = {
  tagSet: 'subject' | 'trial' | string[],
  tags: string[],
  tagValues: { [key: string]: number },
  onTagsChanged: (tags: string[]) => void,
  onTagValuesChanged: (tagValues: { [key: string]: number }) => void,
  onFocus?: () => void,
  onBlur?: () => void,
  hideNumbers?: boolean,
  error?: boolean,
  readonly: boolean
};

const TagEditor = (props: TagEditorProps) => {
  const onChange = (newOptions: MultiValue<Option>) => {
    props.onTagsChanged(newOptions.map(o => o.value));
  }

  function hasUnselectedDescendants(option: Option, selectedOptions: Option[]): boolean {
    // Check if option is selectable and not selected
    if (!option.isNonSelectable && !selectedOptions.some(selectedOption => selectedOption.value === option.value)) {
      return true;
    }
    // Check if any child has unselected descendants
    return option.children?.some(child => hasUnselectedDescendants(child, selectedOptions)) ?? false;
  }
  
  let customStyles;
  if (props.error) {
    customStyles = {
      control: (styles: any) => ({
        ...styles,
        borderColor: 'red',
        '&:hover': {
          borderColor: 'red',
        }
      }),
    };
  }
  else if (props.readonly) {
    customStyles = {
      control: (styles: any) => ({ ...styles, backgroundColor: '#eef2f7', border: '1px solid rgb(222, 226, 230)' })
    };
  }
  else {
    customStyles = {
      control: (styles: any) => ({ ...styles, backgroundColor: 'white', border: '1px solid rgb(222, 226, 230)' }),
    };
  }

  customStyles = {
    ...customStyles,
    option: (provided:any, state:any) => ({
      ...provided,
      cursor: state.isDisabled ? 'cursor' : 'pointer',
      opacity: 1,
      color: "gray",
      backgroundColor: state.isDisabled ? 'ghostwhite' : 'default',
      ':hover': {
        backgroundColor: state.isDisabled ? 'ghostwhite' : 'aliceblue',
      },
      paddingLeft: state.isSelected ? '0.5em' : (state.data.level * 1.5 + 0.5) + 'em',
      display: hasUnselectedDescendants(state.data, selectedOptions) ?  'default' : 'none',
    }),
  };

  const onChangeOption = (option: Option, newValue: number) => {
    let newValues = { ...props.tagValues };
    newValues[option.value] = newValue;
    props.onTagValuesChanged(newValues);
  }

  let optionList: Option[] = [];
  if (props.tagSet === 'subject') optionList = flattenOptions(subjectOptions);
  else if (props.tagSet === 'trial') optionList = flattenOptions(trialOptions);
  else {
    for (let key of props.tagSet) {
      optionList.push({
        value: key,
        label: key
      });
    }
  }

  const selectedOptions = props.tags.flatMap(key => {
    return optionList.filter(o => o.value === key);
  });

  return (
    <div className={"TagEditor"}>
      <Select
        isMulti
        isSearchable
        isDisabled={props.readonly}
        styles={customStyles}
        components={{ MultiValueLabel, NoOptionsMessage }}
        value={selectedOptions}
        onChange={onChange}
        onFocus={props.onFocus}
        onBlur={props.onBlur}
        // @ts-ignore
        onChangeOption={onChangeOption}
        // @ts-ignore
        numberValues={props.tagValues}
        // @ts-ignore
        hideNumbers={props.hideNumbers}
        options={optionList}
        noOptionsMessage={() => {
          return "No tags match your search. We use structured tags, instead of free form text notes, to avoid accidentally hosting Personally Identifiable Information (PII) on the platform. If you don't find the tags you need, feel free to tweet at @KeenonWerling and suggest new tags!";
        }}
        getOptionLabel={getOptionLabel}
        getOptionValue={getOptionValue}
        formatOptionLabel={formatOptionLabel}
        // @ts-ignore
        isOptionDisabled={(option) => option.isNonSelectable}
      />
    </div>
  );
};

export default TagEditor;
