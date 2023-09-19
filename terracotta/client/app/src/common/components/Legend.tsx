import * as React from 'react'
import { Box, TextField } from '@mui/material'

const styles = {
	inputBox: {
		width: 50,
	},
}

const colorbarStyle = {
	width: '100%',
	height: 6,
	borderRadius: 4,
}

export type LegendProps = {
	src: string
	/**
	 * Min/Max range for the Legend ticks.
	 */
	range?: number[] | undefined

	onGetRange: (val: number[]) => void
}

const Legend: React.FC<LegendProps> = ({ src, range, onGetRange }) => (
	<Box sx={{ width: '100%' }}>
		<Box alt="" component="img" src={src} sx={colorbarStyle} />
		{range?.[0] !== undefined && range?.[1] !== undefined && (
			<Box display="flex" justifyContent="space-between">
				<Box sx={styles.inputBox}>
					<TextField
						type="number"
						value={Number(range[0].toFixed(3))}
						variant="standard"
						fullWidth
						onChange={(e) =>
							onGetRange([Number(e.target.value), Number(range[1])])
						}
					/>
				</Box>
				<Box sx={styles.inputBox}>
					<TextField
						type="number"
						value={Number(range[1].toFixed(3))}
						variant="standard"
						fullWidth
						onChange={(e) =>
							onGetRange([Number(range[0]), Number(e.target.value)])
						}
					/>
				</Box>
			</Box>
		)}
	</Box>
)

export default Legend
