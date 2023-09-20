import React, { FC, ReactNode } from 'react'
import { Box, Typography, CircularProgress } from '@mui/material'

const styles = {
	wrapper: {
		m: 2,
		pb: 2,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3',
	},
	spinner: {
		width: '16px !important',
		height: '16px !important',
		ml: 1,
	},
}

interface Props {
	isLoading?: boolean
	title: string
	children: ReactNode
}
const SidebarItemWrapper: FC<Props> = ({ isLoading, title, children }) => (
	<Box sx={styles.wrapper}>
		<Box alignItems="center" display="flex" mb={1}>
			<Typography fontWeight="normal" variant="h4">
				{title}
			</Typography>
			{isLoading && <CircularProgress color="primary" sx={styles.spinner} />}
		</Box>
		{children}
	</Box>
)

export default SidebarItemWrapper
