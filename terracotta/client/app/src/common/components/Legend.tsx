import * as React from 'react';
import { Box, TextField } from '@material-ui/core';
import { makeStyles } from "@material-ui/core/styles"

const useStyles = makeStyles(() => ({
  inputBox: {
    width: 50,
  }
}))

const colorbarStyle = {
  width: '100%',
  height: 6,
  borderRadius: 4,
};

export type LegendProps = {
  src: string;
  /**
   * *Only relevant when `range` is present. Represents the amount of ticks distributed between min/max values(including them).
   */
  length?: number | undefined;
  /**
   * Min/Max range for the Legend ticks.
   */
  range?: number[] | undefined;
  /**
   * Append a unit at the end of the values. (%, °C, £, $)
   */
  unit?: string | undefined;
  onGetRange: (val: number[]) => void
};

const Legend: React.FC<LegendProps> = ({ src, range, onGetRange }) => {
  const classes = useStyles()

  return (
    <Box style={{ width: '100%' }}>
      <img src={src} alt="" style={colorbarStyle} />
      {
        range?.[0] !== undefined &&
        range?.[1] !== undefined && (
          <Box display="flex" justifyContent="space-between">
            <Box className={classes.inputBox}>
              <TextField 
                fullWidth
                type={'number'}
                variant={'standard'}
                value={Number(range[0].toFixed(3))}
                onChange={(e) => onGetRange([Number(e.target.value), Number(range[1])])}
              />
            </Box>
            <Box className={classes.inputBox}>
              <TextField 
                fullWidth
                type={'number'}
                variant={'standard'}
                value={Number(range[1].toFixed(3))}
                onChange={(e) => onGetRange([Number(range[0]), Number(e.target.value)])}
              />
            </Box>
          </Box>
        )
      }
    </Box>
  );
};

export default Legend;
