import React, { FC, ReactNode } from 'react'
import { Paper, Box } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles(({ breakpoints }) => ({
	rooterThanRoot: {
		[ breakpoints.down('xs') ]: {
			width: '100%',
			height: '50%',
		},
	},
	root: {
		// overflowX: 'auto',
		overflowY: 'auto',
		height: '100%',
		width: '30vw',
		minWidth: 360,
		[ breakpoints.down('xs') ]: {
			width: '100%',
		},
	},
	leftBorder: {
		borderLeft: '1px solid #DBE4E9',
	},
	topBorder: {
		borderTop: '1px solid #DBE4E9',
	},
}))

interface Props {
	children?: ReactNode,
}
const SidebarContent: FC<Props> = ({
	children,
}) => {

	const classes = useStyles()

	return (
		<Box className={classes.rooterThanRoot}>
			<Paper className={classes.root}>
				{children}
			</Paper>
		</Box>
	)

}

export default SidebarContent
