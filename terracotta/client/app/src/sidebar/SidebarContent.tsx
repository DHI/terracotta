import React, { FC, ReactNode, useState } from 'react'
import { Paper, Box } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import VerticalHandle from "./VerticalHandle/VerticalHandle"

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
	const [width, setWidth] = useState(30/100 * window.innerWidth)

	return (
		<>
			<VerticalHandle
				boxWidth={width}
				onDrag={setWidth}
				minSize={200}
				minMapSize={40 / 100 * window.innerWidth}
			/>
			<Box className={classes.rooterThanRoot}>
				<Paper className={classes.root} style={{ width: width }}>
					{children}
				</Paper>
			</Box>
		</>
	)

}

export default SidebarContent
