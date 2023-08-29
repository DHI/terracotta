import React, { FC, MouseEvent } from 'react'
import { Box, IconButton } from '@mui/material'
import {
	ChevronLeft,
	ChevronRight,
	ExpandLess,
	ExpandMore,
} from '@mui/icons-material'
import { makeStyles } from '@mui/material/styles'
import useIsMobileWidth from '../common/hooks/useIsMobileWidth'

const iconStyles = {
	icon: {
		backgroundColor: '#fff',
		height: 22,
	},
	activeIcon: {
		backgroundColor: '#0b4566',
		'& path': {
			fill: '#fff',
		},
	},
}

const styles = {
	leftBorder: {
		borderLeft: '1px solid #DBE4E9',
	},
	topBorder: {
		borderTop: '1px solid #DBE4E9',
	},
	noRadius: {
		borderRadius: 0,
		width: 36,
		height: 36,
	},
	iconWrapper: {
		flexDirection: 'column',
		height: 'calc(100% - 72px)',
		'@media (max-width: 600px)': {
			flexDirection: 'row',
			height: 'auto',
		},
	},
	tooltipStyle: {
		display: {
			xs: 'none',
			sm: 'block',
		},
	},
}

interface Props {
	toggleSidebarOpen: (event: MouseEvent<HTMLElement>) => void
	isSidebarOpen: boolean
}

const SidebarControl: FC<Props> = ({ toggleSidebarOpen, isSidebarOpen }) => {
	const isMobile = useIsMobileWidth()

	const rootClass = isMobile ? styles.topBorder : styles.leftBorder

	return (
		<Box
			display="flex"
			flexDirection={isMobile ? 'row' : 'column'}
			height={1}
			sx={rootClass}
		>
			<Box display="flex" justifyContent="center">
				<IconButton
					sx={{ backgroundColor: '#fff' }}
					onClick={toggleSidebarOpen}
				>
					{isSidebarOpen && !isMobile && (
						<ChevronRight color="primary" sx={iconStyles.icon} />
					)}
					{!isSidebarOpen && !isMobile && (
						<ChevronLeft color="primary" sx={iconStyles.icon} />
					)}
					{isSidebarOpen && isMobile && (
						<ExpandMore color="primary" sx={iconStyles.icon} />
					)}
					{!isSidebarOpen && isMobile && (
						<ExpandLess color="primary" sx={iconStyles.icon} />
					)}
				</IconButton>
			</Box>
		</Box>
	)
}

export default SidebarControl
