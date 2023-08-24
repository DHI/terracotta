import React, { FC } from "react";
import {
	TableRow as MuiTableRow,
	TableCell,
	Box,
	IconButton,
} from "@mui/material";
import { makeStyles } from "@mui/material/styles";
import { DatasetItem } from "../common/data/getData";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

const styles = {
	tableCell: {
		padding: 6,
		borderBottom: "none",
	},
	tableRow: {
		cursor: "pointer",
	},
	icon: {
		width: 18,
		height: 18,
	},
	iconChecked: {
		color: "#61C051",
	},
	noPadding: {
		padding: 0,
	},
};

interface Props {
	dataset: DatasetItem;
	keyVal: string;
	checked: boolean;
	onClick?: () => void;
	onMouseEnter?: () => void;
	onMouseLeave?: () => void;
}

const TableRow: FC<Props> = ({
	dataset,
	keyVal,
	checked,
	onClick,
	onMouseEnter,
	onMouseLeave,
}) => {
	return (
		<MuiTableRow
			hover
			onClick={onClick}
			sx={styles.tableRow}
			onMouseEnter={onMouseEnter}
			onMouseLeave={onMouseLeave}
		>
			<TableCell sx={styles.tableCell}>
				<Box display={"flex"} alignItems={"center"}>
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
				<TableCell sx={styles.tableCell} key={`${keyVal}-cell-${i}`}>
					{dataset[item]}
				</TableCell>
			))}
		</MuiTableRow>
	);
};

export default TableRow;
