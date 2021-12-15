import React, { FC, MouseEvent } from 'react'
import {
	Box,
	IconButton,
} from '@material-ui/core'
import {
	ChevronLeft,
	ChevronRight,
	ExpandLess,
	ExpandMore,
} from '@material-ui/icons'
import { makeStyles } from '@material-ui/core/styles'
import useIsMobileWidth from '../common/hooks/useIsMobileWidth'

const iconStyle = makeStyles({
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
})

const useStyles = makeStyles(theme => ({
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
		[ theme.breakpoints.down('sm') ]: {
			display: 'none',
		},
	},
}))

interface Props {
	toggleSidebarOpen: (event: MouseEvent<HTMLElement>) => void,
	isSidebarOpen: boolean,
}

const SidebarControl: FC<Props> = ({
	toggleSidebarOpen,
	isSidebarOpen,
}) => {

	const {
		leftBorder, topBorder
	} = useStyles()
	const { icon } = iconStyle()
	const isMobile = useIsMobileWidth()

	const rootClass = isMobile ? topBorder : leftBorder

	return (
		<Box
			className={rootClass}
			display={'flex'}
			height={1}
			flexDirection={isMobile ? 'row' : 'column'}
		>
			<Box display={'flex'} justifyContent={'center'}>
				<IconButton
					onClick={toggleSidebarOpen}
					style={{ backgroundColor: '#fff' }}
				>
					{isSidebarOpen && !isMobile && (
					<ChevronRight className={icon} color={'primary'} />
					)}
					{!isSidebarOpen && !isMobile && (
					<ChevronLeft className={icon} color={'primary'} />
					)}
					{isSidebarOpen && isMobile && (
					<ExpandMore className={icon} color={'primary'} />
					)}
					{!isSidebarOpen && isMobile && (
					<ExpandLess className={icon} color={'primary'} />
					)}
				</IconButton>
			</Box>
		</Box>
	)

}

export default SidebarControl
