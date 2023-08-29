import React, { FC, CSSProperties, useContext } from 'react'
import AddIcon from '@mui/icons-material/Add'
import RemoveIcon from '@mui/icons-material/Remove'
import PublicIcon from '@mui/icons-material/Public'
import StreetviewIcon from '@mui/icons-material/Streetview'
import { IconButton, Grid, Tooltip } from '@mui/material'
import { makeStyles } from '@mui/material/styles'
import AppContext from '../AppContext'
import { Viewport } from './types'

const styles = {
	iconButton: {
		p: 0,
	},
	icon: {
		backgroundColor: '#fff',
		height: 36,
		width: 36,
		fill: '#0B4566',
		p: 1,
		boxSizing: 'border-box',
		'&:hover': {
			backgroundColor: 'primary.main',
		},
	},
	activeIcon: {
		backgroundColor: '#0b4566',
		'& path': {
			fill: '#fff',
		},
		height: 36,
		width: 36,
		p: 1,
		boxSizing: 'border-box',
	},
}

const gridStyle = {
	position: 'fixed',
	left: 0,
	top: '50%',
	width: 36,
	boxShadow: 'rgba(0, 0, 0, 0.16) 4px 0px 4px',
	zIndex: 100,
	transform: 'translate(0, -50%)',
}

const ZoomControl: FC = () => {
	const {
		state: { isOpticalBasemap },
		actions: { setIsOpticalBasemap, setViewport },
	} = useContext(AppContext)

	return (
		<Grid sx={gridStyle} container>
			<Grid container>
				<Tooltip placement="right" title="Change base map">
					<IconButton
						sx={styles.iconButton}
						onClick={() => setIsOpticalBasemap(!isOpticalBasemap)}
					>
						{!isOpticalBasemap ? (
							<StreetviewIcon sx={styles.icon} />
						) : (
							<PublicIcon sx={styles.icon} />
						)}
						{/* <PublicIcon
              className={!isOpticalBasemap ? classes.icon : classes.activeIcon}
            /> */}
					</IconButton>
				</Tooltip>
			</Grid>
			<Grid container>
				<IconButton
					sx={styles.iconButton}
					onClick={() =>
						setViewport((v: Viewport) => ({ ...v, zoom: Number(v.zoom) + 1 }))
					}
				>
					<AddIcon sx={styles.icon} />
				</IconButton>
			</Grid>
			<Grid container>
				<IconButton
					sx={styles.iconButton}
					onClick={() =>
						setViewport((v: Viewport) => ({ ...v, zoom: Number(v.zoom) - 1 }))
					}
				>
					<RemoveIcon sx={styles.icon} />
				</IconButton>
			</Grid>
		</Grid>
	)
}

export default ZoomControl
