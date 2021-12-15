import React, { useState, useEffect } from 'react';
import { Slider as MSlider, Box, Grid, Typography, TextField } from '@material-ui/core';

type SliderProps = {
  /**
   * Default values of the slider in format `[min, max]` or `number`.
   */
  defaultValue: number[] | number;
  title?: string | undefined;
  min?: number | undefined;
  max?: number | undefined;
  step?: number | undefined;
  /**
   * Get the value while using the slider thumb.
   */
  getValue?: (val: number | number[]) => void;
  /**
   * Get the value once you release the slider thumb.
   */
  getValueCommitted?: (val: number | number[]) => void;
  /**
   * *Requires `title` prop. Counted in `rem` units.
   */
  sliderMarginLeft?: number | undefined;
  noNumbers?: boolean | undefined;
  /**
   * Append a unit at the end of the values. (%, /10, £, $)
   */
  unit?: string | undefined;
  disabled?: boolean
};

const Slider: React.FC<SliderProps> = ({
  defaultValue = [0, 1],
  title,
  min = 0,
  max = 1,
  step = 0.01,
  getValue,
  getValueCommitted,
  sliderMarginLeft = 1,
  noNumbers = false,
  unit = '',
  disabled
}) => {
  const [value, setValue] = useState(defaultValue);

  const handleChange = (newValue: number | number[]) => {

    setValue(newValue);
    getValue && getValue(newValue);

  };

  useEffect(() => {
    
    setValue(defaultValue)

  }, [defaultValue])

  useEffect(() => {

  }, [min, max])

  return (
    <Grid
      container
      direction="row"
      alignItems="center"
      justify="center"
      wrap="nowrap"
    >
      {title && (
        <Box>
          <Grid
            container
            alignItems="center"
            style={{
              height: '100%',
              marginRight: noNumbers ? '1rem' : '0rem',
            }}
          >
            <Typography variant="h5">{title}</Typography>
          </Grid>
        </Box>
      )}
      {!noNumbers && Array.isArray(value) && typeof value[0] === 'number' && (
        <Box style={{ marginLeft: title ? `${sliderMarginLeft}rem` : '0rem' }}>
          <Grid
            container
            alignItems="center"
            justify="center"
            style={{ height: '100%', maxWidth: '8rem' }}
          >
            <TextField 
              fullWidth
              type={'number'}
              variant={'standard'}
              value={Number(value[0].toFixed(3))}
              onChange={(e) => getValueCommitted && getValueCommitted([Number(e.target.value), value[1]])}
            />
          </Grid>
        </Box>
      )}

      <MSlider
        style={{ margin: '0rem .6rem', width: '100%' }}
        value={value}
        min={min}
        step={step}
        max={max}
        scale={(x) => x / 10}
        onChange={(e, val) => handleChange(val)}
        onChangeCommitted={(e, val) =>
          getValueCommitted && getValueCommitted(val)
        }
        valueLabelDisplay="off"
        disabled={disabled}
      />
      {!noNumbers && Array.isArray(value) && (
        <Box>
          <Grid
            container
            alignItems="center"
            justify="center"
            style={{ height: '100%', maxWidth: '8rem' }}
          >
            <TextField 
              fullWidth
              type={'number'}
              variant={'standard'}
              value={Number(value[1].toFixed(3)) || (!Array.isArray(value) && Number((value as number).toFixed(3)))}
              onChange={(e) => getValueCommitted && getValueCommitted([value[0], Number(e.target.value)])}
            />
          </Grid>
        </Box>
      )}
    </Grid>
  );
};

export default Slider;
