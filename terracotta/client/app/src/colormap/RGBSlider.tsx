import React, { FC, useEffect, useState } from 'react'
import {
	Box,
	Grid,
	FormControl,
	Select,
	MenuItem,
	InputLabel,
} from '@mui/material'
import Slider from '../common/components/Slider'

interface Props {
	options?: string[]
	selectValue?: string
	onGetSelectValue: (val: string) => void
	sliderValue: number[]
	onGetSliderValue: (val: number[]) => void
	min: number
	max: number
	title: string
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
	step,
}) => {
	const [localRange, setLocalRange] = useState(sliderValue)
	useEffect(() => {
		setLocalRange(sliderValue)
	}, [sliderValue])
	return (
		<Grid alignItems="center" container>
			<Grid alignItems="center" xs={2} container item>
				<FormControl sx={{ display: 'flex', alignItems: 'center' }} fullWidth>
					<InputLabel>Band</InputLabel>
					<Select
						id="demo-simple-select-outlined"
						size="small"
						value={selectValue || ''}
						fullWidth
						onChange={(e) => onGetSelectValue(String(e.target.value))}
					>
						{options?.map((option: string) => (
							<MenuItem key={`limit-${option}`} value={option}>
								{option}
							</MenuItem>
						))}
					</Select>
				</FormControl>
			</Grid>
			<Grid alignItems="center" xs={10} container item>
				<Box ml={2} mt={2} width={1}>
					<Slider
						defaultValue={localRange}
						getValue={(value: number | number[]) =>
							Array.isArray(value) && setLocalRange(value)
						}
						getValueCommitted={(value) =>
							Array.isArray(value) && onGetSliderValue(value)
						}
						max={max}
						min={min}
						step={step}
						title={title}
					/>
				</Box>
			</Grid>
		</Grid>
	)
}

export default RGBSlider
