import React, { FC, useContext, useEffect } from 'react'
import { Box } from '@mui/material'
import AppContext from '../AppContext'
import RGBSlider from './RGBSlider'

const RGBSelector: FC = () => {
	const {
		state: { datasetBands, activeRGB, activeDataset, datasets, page, limit },
		actions: { setActiveRGB },
	} = useContext(AppContext)

	useEffect(() => {}, [])

	const datasetPageRange =
		activeDataset !== undefined &&
		datasets?.[activeDataset - page * limit]?.range
	const minRange = datasetPageRange && datasetPageRange[0]
	const maxRange = datasetPageRange && datasetPageRange[1]

	const onGetBandValue = (val: string, bandKey: string) => {
		setActiveRGB(
			(prev) =>
				prev && {
					...prev,
					[bandKey]: { band: val, range: prev[bandKey].range },
				},
		)
	}

	const onGetSliderValue = (val: number[], sliderKey: string) => {
		setActiveRGB(
			(prev) =>
				prev && {
					...prev,
					[sliderKey]: { range: val, band: prev[sliderKey].band },
				},
		)
	}

	return (
		<Box>
			{datasetBands &&
				activeRGB &&
				Object.keys(activeRGB).map((color: string) => (
					<Box key={color} mb={1}>
						<RGBSlider
							key={`rgb-slider-${color}`}
							max={Number(maxRange)}
							min={Number(minRange)}
							options={datasetBands}
							selectValue={activeRGB[color].band}
							sliderValue={[
								Number(activeRGB[color].range?.[0]),
								Number(activeRGB[color].range?.[1]),
							]}
							step={0.01}
							title={`${color}:`}
							onGetSelectValue={(val) => onGetBandValue(val, color)}
							onGetSliderValue={(val) => onGetSliderValue(val, color)}
						/>
					</Box>
				))}
		</Box>
	)
}

export default RGBSelector
