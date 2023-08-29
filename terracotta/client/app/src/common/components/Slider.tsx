import React, { useState, useEffect } from 'react'
import {
	Slider as MSlider,
	Box,
	Grid,
	Typography,
	TextField,
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

	useEffect(() => {}, [min, max])

	return (
		<Grid
			alignItems="center"
			direction="row"
			justifyContent="center"
			wrap="nowrap"
			container
		>
			{title && (
				<Box>
					<Grid
						alignItems="center"
						sx={{
							height: '100%',
							mr: noNumbers ? '1rem' : '0rem',
						}}
						container
					>
						<Typography variant="body2">{title}</Typography>
					</Grid>
				</Box>
			)}
			{!noNumbers && Array.isArray(value) && typeof value[0] === 'number' && (
				<Box sx={{ ml: title ? `${sliderMarginLeft}rem` : '0rem' }}>
					<Grid
						alignItems="center"
						justifyContent="center"
						sx={{ height: '100%', maxWidth: '8rem' }}
						container
					>
						<TextField
							size="small"
							type="number"
							value={Number(value[0].toFixed(3))}
							variant="standard"
							fullWidth
							onChange={(e) =>
								getValueCommitted &&
								getValueCommitted([Number(e.target.value), value[1]])
							}
						/>
					</Grid>
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
				<Box>
					<Grid
						alignItems="center"
						justifyContent="center"
						sx={{ height: '100%', maxWidth: '8rem' }}
						container
					>
						<TextField
							size="small"
							type="number"
							value={
								Number(value[1].toFixed(3)) ||
								(!Array.isArray(value) && Number((value as number).toFixed(3)))
							}
							variant="standard"
							fullWidth
							onChange={(e) =>
								getValueCommitted &&
								getValueCommitted([value[0], Number(e.target.value)])
							}
						/>
					</Grid>
				</Box>
			)}
		</Grid>
	)
}

export default Slider
