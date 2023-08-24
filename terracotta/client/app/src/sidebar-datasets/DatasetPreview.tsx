import React, { FC } from "react";
import {
	Box,
	TableRow,
	TableCell,
	Grid,
	Collapse,
	Typography,
	Link,
} from "@mui/material";
import { makeStyles } from "@mui/material/styles";
import { ResponseMetadata200 } from "../common/data/getData";
import CopyToClipboard from "../common/components/CopyToClipboard";

const styles = {
	imagePreview: {
		height: "90%",
		width: "auto",
	},
	codeContainer: {
		backgroundColor: "#F8F8F8",
		overflowX: "auto",
		width: "fit-content",
		maxWidth: "100%",
	},
	codeContainerText: {
		color: "#557A8F",
		fontSize: 11,
	},
	copyTooltip: {
		cursor: "pointer",
	},
	tableCell: {
		padding: 0,
	},
	metadataLink: {
		fontSize: 10,
		color: "#86A2B3",
	},
};

interface Props {
	host: string;
	page: number;
	limit: number;
	i: number;
	activeDataset?: number;
	dataset: ResponseMetadata200;
	datasetUrl?: string;
}
const DatasetPreview: FC<Props> = ({
	host,
	page,
	limit,
	i,
	activeDataset,
	dataset,
	datasetUrl,
}) => {
	const returnJson = () =>
		Object.keys(dataset)
			.reduce((acc: string[], keyItem: string) => {
				const neededKeys = ["mean", "range", "stdev", "valid_percentage"];
				if (neededKeys.includes(keyItem)) {
					if (keyItem === "range") {
						const buildStr = `  ${keyItem}: [${dataset[keyItem]}],\n`;
						acc = [...acc, buildStr];
					} else {
						const buildStr = `  ${keyItem}: ${dataset[keyItem]},\n`;
						acc = [...acc, buildStr];
					}
				}

				return acc;
			}, [])
			.join("");

	return (
		<TableRow>
			<TableCell sx={styles.tableCell} colSpan={8}>
				<Collapse
					in={page * limit + i === activeDataset}
					timeout="auto"
					unmountOnExit
				>
					{datasetUrl && (
						<Box p={1} sx={styles.codeContainer}>
							<Box width={1} display={"flex"} alignItems={"center"}>
								<Typography sx={styles.codeContainerText}>
									<code>{"Raster url\n"}</code>
								</Typography>
								<Box>
									<CopyToClipboard
										sx={styles.copyTooltip}
										helperText={"Copy to clipboard"}
										message={datasetUrl}
									/>
								</Box>
							</Box>
							<code style={{ wordBreak: "break-all" }}>{datasetUrl}</code>
						</Box>
					)}
					<Box my={1}>
						<Grid container alignItems={"center"}>
							<Grid item xs={6}>
								<Box p={1} sx={styles.codeContainer}>
									<Typography sx={styles.codeContainerText}>
										<code>{"Metadata"}</code>
									</Typography>
									<code style={{ whiteSpace: "pre" }}>
										{"{\n"}
										{returnJson()}
										{"}\n"}
									</code>
									<Link
										target={"_blank"}
										href={`${host}/metadata${Object.keys(dataset.keys)
											.map((keyItem: string) => `/${dataset.keys[keyItem]}`)
											.join("")}`}
										sx={styles.metadataLink}
									>
										{"View full metadata\n"}
									</Link>
								</Box>
							</Grid>
							<Grid
								item
								xs={6}
								container
								justifyContent={"center"}
								alignItems={"center"}
							>
								<Box p={1}>
									<Box
										component="img"
										src={`${host}/singleband/${Object.keys(dataset.keys)
											.map(
												(datasetKey: string) => `${dataset.keys[datasetKey]}/`,
											)
											.join("")}preview.png?tile_size=[128,128]`}
										alt={"TC-preview"}
										sx={styles.imagePreview}
										loading={"eager"}
									/>
								</Box>
							</Grid>
						</Grid>
					</Box>
				</Collapse>
			</TableCell>
		</TableRow>
	);
};

export default DatasetPreview;
