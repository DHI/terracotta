import React, { useState, useEffect } from 'react'
import {
	Slider as MSlider,
	Box,
	Grid,
	Typography,
	TextField,
	Stack,
} from '@mui/material'

type SliderProps = {
	/**
	 * Default values of the slider in format `[min, max]` or `number`.
	 */
	defaultValue: number[] | number
	title?: string | undefined
	min?: number | undefined
	max?: number | undefined
	step?: number | undefined
	/**
	 * Get the value while using the slider thumb.
	 */
	getValue?: (val: number | number[]) => void
	/**
	 * Get the value once you release the slider thumb.
	 */
	getValueCommitted?: (val: number | number[]) => void
	/**
	 * *Requires `title` prop. Counted in `rem` units.
	 */
	sliderMarginLeft?: number | undefined
	noNumbers?: boolean | undefined
	/**
	 * Append a unit at the end of the values. (%, /10, £, $)
	 */
	unit?: string | undefined
	disabled?: boolean
}

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
	disabled,
}) => {
	const [value, setValue] = useState(defaultValue)

	const handleChange = (newValue: number | number[]) => {
		setValue(newValue)
		if (getValue) {
			getValue(newValue)
		}
	}

	useEffect(() => {
		setValue(defaultValue)
	}, [defaultValue])

	return (
		<Stack alignItems="center" direction="row" gap={1} justifyContent="center">
			{title && (
				<Typography
					minWidth="5%"
					mr={title ? 1 : 0}
					variant="body2"
					width="fit-content"
				>
					{title}
				</Typography>
			)}
			{!noNumbers && Array.isArray(value) && typeof value[0] === 'number' && (
				<Box maxWidth="5rem">
					<TextField
						inputProps={{
							style: {
								textAlign: 'center',
							},
						}}
						size="small"
						type="number"
						value={Number(value[0].toFixed(3))}
						variant="outlined"
						fullWidth
						onChange={(e) =>
							getValueCommitted &&
							getValueCommitted([Number(e.target.value), value[1]])
						}
					/>
				</Box>
			)}

			<MSlider
				color="secondary"
				disabled={disabled}
				max={max}
				min={min}
				scale={(x) => x / 10}
				size="small"
				step={step}
				sx={{ m: '0rem .6rem', width: '100%' }}
				value={value}
				valueLabelDisplay="off"
				onChange={(e, val) => handleChange(val)}
				onChangeCommitted={(e, val) =>
					getValueCommitted && getValueCommitted(val)
				}
			/>
			{!noNumbers && Array.isArray(value) && (
				<Box maxWidth="5rem">
					<TextField
						inputProps={{
							style: {
								textAlign: 'center',
							},
						}}
						size="small"
						type="number"
						value={
							Number(value[1].toFixed(3)) ||
							(!Array.isArray(value) && Number((value as number).toFixed(3)))
						}
						variant="outlined"
						fullWidth
						onChange={(e) =>
							getValueCommitted &&
							getValueCommitted([value[0], Number(e.target.value)])
						}
					/>
				</Box>
			)}
		</Stack>
	)
}

export default Slider
