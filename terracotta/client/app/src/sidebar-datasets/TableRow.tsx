import React, { FC } from 'react'
import {
	TableRow as MuiTableRow,
	TableCell,
	Box,
	IconButton,
} from '@mui/material'
import { makeStyles } from '@mui/material/styles'
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import { DatasetItem } from '../common/data/getData'

const styles = {
	tableCell: {
		p: 1,
		borderBottom: 'none',
	},
	tableRow: {
		cursor: 'pointer',
	},
	icon: {
		width: 18,
		height: 18,
	},
	iconChecked: {
		color: '#61C051',
	},
	noPadding: {
		p: 0,
	},
}

interface Props {
	dataset: DatasetItem
	keyVal: string
	checked: boolean
	onClick?: () => void
	onMouseEnter?: () => void
	onMouseLeave?: () => void
}

const TableRow: FC<Props> = ({
	dataset,
	keyVal,
	checked,
	onClick,
	onMouseEnter,
	onMouseLeave,
}) => (
	<MuiTableRow
		sx={styles.tableRow}
		hover
		onClick={onClick}
		onMouseEnter={onMouseEnter}
		onMouseLeave={onMouseLeave}
	>
		<TableCell sx={styles.tableCell}>
			<Box alignItems="center" display="flex">
				{checked ? (
					<IconButton sx={{ root: styles.noPadding }}>
						<CheckCircleIcon sx={{ ...styles.iconChecked, ...styles.icon }} />
					</IconButton>
				) : (
					<IconButton sx={{ root: styles.noPadding }}>
						<RadioButtonUncheckedIcon sx={styles.icon} />
					</IconButton>
				)}
			</Box>
		</TableCell>
		{Object.keys(dataset).map((item: string, i: number) => (
			<TableCell key={`${keyVal}-cell-${i}`} sx={styles.tableCell}>
				{dataset[item]}
			</TableCell>
		))}
	</MuiTableRow>
)

export default TableRow
