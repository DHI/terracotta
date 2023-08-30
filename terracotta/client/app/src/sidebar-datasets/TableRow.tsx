import React, { FC } from 'react'
import {
	TableRow as MuiTableRow,
	TableCell,
	Box,
	IconButton,
	Typography,
} from '@mui/material'
import { makeStyles } from '@mui/material/styles'
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import { DatasetItem, KeyItem } from '../common/data/getData'

const styles = {
	tableCell: {
		borderBottom: '1px solid',
		borderBottomColor: 'divider',
		height: 'fit-content',
		py: '6px',
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
		p: '0px',
	},
}

interface Props {
	keys: KeyItem[]
	dataset: DatasetItem
	keyVal: string
	checked: boolean
	onClick?: () => void
	onMouseEnter?: () => void
	onMouseLeave?: () => void
}

const TableRow: FC<Props> = ({
	keys,
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
			{checked ? (
				<IconButton sx={styles.noPadding}>
					<CheckCircleIcon sx={{ ...styles.iconChecked, ...styles.icon }} />
				</IconButton>
			) : (
				<IconButton sx={styles.noPadding}>
					<RadioButtonUncheckedIcon sx={styles.icon} />
				</IconButton>
			)}
		</TableCell>
		{keys.map((key, i: number) => (
			<TableCell key={`${keyVal}-cell-${i}`} sx={styles.tableCell}>
				<Typography variant="body2">{dataset[key.original]}</Typography>
			</TableCell>
		))}
	</MuiTableRow>
)

export default TableRow
