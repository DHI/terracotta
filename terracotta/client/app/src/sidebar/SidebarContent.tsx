import React, { FC, ReactNode, useState } from 'react'
import { Paper, Box } from '@mui/material'
import VerticalHandle from './VerticalHandle/VerticalHandle'

const styles = {
	rooterThanRoot: {
		width: '100%',
		height: '100%',
		xs: {
			width: '100%',
			height: '50%',
		},
	},
	root: {
		overflowY: 'auto',
		height: '100%',
		xs: {
			width: '100%',
		},
	},
	leftBorder: {
		borderLeft: '1px solid #DBE4E9',
	},
	topBorder: {
		borderTop: '1px solid #DBE4E9',
	},
}

interface Props {
	children?: ReactNode
}
const SidebarContent: FC<Props> = ({ children }) => {
	const [width, setWidth] = useState((30 / 100) * window.innerWidth)

	return (
		<>
			<VerticalHandle
				boxWidth={width}
				minMapSize={(40 / 100) * window.innerWidth}
				minSize={200}
				onDrag={setWidth}
			/>
			<Box sx={styles.rooterThanRoot}>
				<Paper sx={{ ...styles.root, width }}>{children}</Paper>
			</Box>
		</>
	)
}

export default SidebarContent
