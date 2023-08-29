import React, { FC, useContext } from 'react'
import {
	Box,
	Typography,
	Collapse,
	FormControl,
	Select,
	MenuItem,
} from '@mui/material'
import { makeStyles } from '@mui/material/styles'
import SinglebandSelector from './SinglebandSelector'
import RGBSelector from './RGBSelector'
import AppContext from '../AppContext'
import endpoints, { Endpoint } from './endpoints'

const styles = {
	wrapper: {
		m: 2,
		pb: 2,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3',
	},
	rgbText: {
		fontSize: 12,
		mr: 1,
	},
}

const DatasetsColormap: FC = () => {
	const {
		state: { activeDataset, activeEndpoint },
		actions: { setActiveEndpoint },
	} = useContext(AppContext)

	return (
		<Collapse in={activeDataset !== undefined} timeout="auto" unmountOnExit>
			<Box sx={styles.wrapper}>
				<Box
					alignItems="center"
					display="flex"
					justifyContent="space-between"
					mb={1}
				>
					<Typography variant="body1">Customize layer</Typography>
					<Box alignItems="center" display="flex" sx={{ minWidth: 100 }}>
						<FormControl fullWidth>
							<Select
								id="demo-simple-select-outlined"
								value={activeEndpoint}
								fullWidth
								onChange={(e) => setActiveEndpoint(String(e.target.value))}
							>
								{endpoints.map((option: Endpoint) => (
									<MenuItem key={`endpoint-${option.id}`} value={option.id}>
										{option.id}
									</MenuItem>
								))}
							</Select>
						</FormControl>
					</Box>
				</Box>
				{activeEndpoint === 'singleband' && <SinglebandSelector />}
				{activeEndpoint === 'rgb' && <RGBSelector />}
			</Box>
		</Collapse>
	)
}

export default DatasetsColormap
