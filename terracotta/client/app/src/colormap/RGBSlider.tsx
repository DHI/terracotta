import React, { FC, useEffect, useState } from 'react'
import { Box, Grid, FormControl, Select, MenuItem, InputLabel } from '@material-ui/core'
import Slider from "../common/components/Slider"

interface Props {
    options?: string[],
    selectValue?: string,
    onGetSelectValue: (val: string) => void,
    sliderValue: number[],
    onGetSliderValue: (val: number[]) => void,
    min: number,
    max: number,
    title: string,
    step: number
}

const RGBSlider: FC<Props> = ({
    options,
    selectValue,
    onGetSliderValue,
    onGetSelectValue,
    min,
    max,
    sliderValue,
    title,
    step
}) => {
    const [ localRange, setLocalRange ] = useState(sliderValue)
    useEffect(() => {
        setLocalRange(sliderValue)
    }, [sliderValue])
    return (
        <Grid container alignItems={'center'}>
            <Grid container item xs={2} alignItems={'center'}>
                <FormControl fullWidth style={{ display: 'flex', alignItems: 'center' }}>
                    <InputLabel style={{ fontSize: 10 }}>
                        {'Band'}
                    </InputLabel>
                    <Select
                        id="demo-simple-select-outlined"
                        value={selectValue || ''}
                        onChange={(e) => onGetSelectValue(String(e.target.value))}
                        fullWidth
                    >
                        {
                            options?.map((option: string) => (
                                <MenuItem key={`limit-${option}`} value={option}>{option}</MenuItem>
                            ))
                        }
                    </Select>
                </FormControl>
            </Grid>
            <Grid container item xs={10} alignItems={'center'}>
                <Box ml={2} mt={2} width={1}>
                    <Slider 
                        getValueCommitted={value => Array.isArray(value) && onGetSliderValue(value)} 
                        getValue={(value: number | number[]) => Array.isArray(value) && setLocalRange(value)}
                        defaultValue={localRange} 
                        min={min} 
                        max={max} 
                        step={step} 
                        title={title}
                    />
                </Box>
            </Grid>
        </Grid>
    )

}

export default RGBSlider
