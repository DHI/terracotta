import React, { FC, useState, useContext, useEffect } from 'react'
import {
	Box,
	FormControl,
	Select,
	MenuItem,
	InputLabel,
	Grid,
} from '@mui/material'
import AppContext from '../AppContext'
import Slider from '../common/components/Slider'
import COLORMAPS, { Colormap } from './colormaps'
import Legend from '../common/components/Legend'

const SinglebandSelector: FC = () => {
	const {
		state: {
			colormap,
			activeDataset,
			page,
			limit,
			datasets,
			activeSinglebandRange,
		},
		actions: { setColormap, setActiveSinglebandRange },
	} = useContext(AppContext)

	const minRange =
		activeDataset !== undefined &&
		datasets?.[activeDataset - page * limit]?.range[0]
	const maxRange =
		activeDataset !== undefined &&
		datasets?.[activeDataset - page * limit]?.range[1]

	const [localRange, setLocalRange] = useState(activeSinglebandRange)
	const onSetColormap = (colorId: string) => {
		const colormapObj = COLORMAPS.find((item: Colormap) => item.id === colorId)
		if (colormapObj) {
			setColormap(colormapObj)
		}
	}

	const onSetRangeValue = (range: number[]) => {
		setActiveSinglebandRange(range)
	}

	useEffect(() => {
		if (activeSinglebandRange) {
			setLocalRange(activeSinglebandRange)
		}
	}, [activeSinglebandRange])

	return (
		<Grid alignItems="center" container>
			<Grid xs={4} item>
				<FormControl fullWidth>
					<InputLabel id="colormap-select">Colormap</InputLabel>
					<Select
						label="Colormap"
						labelId="colormap-select"
						size="small"
						value={colormap.id}
						fullWidth
						onChange={(e) => onSetColormap(String(e.target.value))}
					>
						{COLORMAPS.map((option: Colormap, i: number) => (
							<MenuItem key={`limit-${option.id}`} value={option.id}>
								{option.displayName}
							</MenuItem>
						))}
					</Select>
				</FormControl>
			</Grid>
			<Grid xs={8} item>
				<Box mx={4}>
					{datasets &&
						activeSinglebandRange !== undefined &&
						activeDataset !== undefined && (
							<>
								<Slider
									defaultValue={activeSinglebandRange}
									disabled={minRange === maxRange}
									getValue={(value: number | number[]) => {
										if (Array.isArray(value)) {
											setLocalRange(value as [number, number])
										}
									}}
									getValueCommitted={(value) => {
										if (Array.isArray(value)) {
											onSetRangeValue(value)
										}
									}}
									max={maxRange || 0}
									min={minRange || 0}
									step={0.01}
									title="Contrast"
									noNumbers
								/>
								<Legend
									range={localRange}
									src={colormap.img_url}
									onGetRange={(val) => setActiveSinglebandRange(val)}
								/>
							</>
						)}
				</Box>
			</Grid>
		</Grid>
	)
}

export default SinglebandSelector
