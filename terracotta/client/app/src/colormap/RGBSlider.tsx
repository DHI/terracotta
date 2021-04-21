import React, { FC, useState } from 'react'
import { Box, Grid, FormControl, Select, MenuItem } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import Slider from "../common/components/Slider"

const useStyles = makeStyles(theme => ({

}))

interface Props {
    options: string[],
    selectValue: string,
    onGetSelectValue: (val: string) => void,
    sliderValue: number[],
    onGetSliderValue: (val: number[]) => void,
    min: number,
    max: number,
    title: string
}

const RGBSlider: FC<Props> = ({
    options,
    selectValue,
    onGetSliderValue,
    onGetSelectValue,
    min,
    max,
    sliderValue,
    title
}) => {
    const [ localRange, setLocalRange ] = useState(sliderValue)
    const classes = useStyles()

    return (
        <Grid container>
            <Grid item xs={4}>
                <FormControl fullWidth>
                    <Select
                        id="demo-simple-select-outlined"
                        value={selectValue}
                        onChange={(e) => onGetSelectValue(String(e.target.value))}
                        fullWidth
                    >
                        {
                            options.map((option: string) => (
                                <MenuItem key={`limit-${option}`} value={option}>{option}</MenuItem>
                            ))
                        }
                    </Select>
                </FormControl>
            </Grid>
            <Grid item xs={8}>
                <Slider 
                    getValueCommitted={value => Array.isArray(value) && onGetSliderValue(value)} 
                    getValue={(value: any) => setLocalRange(value)}
                    defaultValue={localRange} 
                    min={0} 
                    max={255} 
                    step={1} 
                    title={title}
                />
            </Grid>
        </Grid>
    )

}

export default RGBSlider
