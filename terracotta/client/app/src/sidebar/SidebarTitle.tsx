import React, { CSSProperties, FC } from "react";
import { Box, Typography, Link, Tooltip } from "@mui/material";
import HeaderImage from "./../common/images/header.svg";
import { KeyItem } from "./../common/data/getData";

const styles = {
	wrapper: {
		margin: 16,
		backgroundColor: "#FFFFFF",
		borderBottom: "1px solid #86A2B3",
	},
	icon: {
		width: 20,
		height: 22,
		"&:hover": {
			opacity: 0.7,
		},
	},
	infoIcon: {
		marginLeft: 4,
	},
	detailsBox: {
		marginTop: 8,
		marginBottom: 8,
		"&:hover": {
			cursor: "pointer",
		},
	},
	detailsText: {
		marginTop: 6,
	},
	hostText: {
		fontSize: 12,
		wordBreak: "break-all",
	},
	hasDescription: {
		cursor: "pointer",
		"&:hover": {
			textDecoration: "underline",
		},
	},
	noDescription: {
		cursor: "default",
	},
};

interface Props {
	host?: string;
	style?: CSSProperties;
	details?: string;
	keys?: KeyItem[];
}
const SidebarTitle: FC<Props> = ({ style, host, keys }) => {
	return (
		<Box style={{ ...style }} sx={styles.wrapper}>
			<Box
				display={"flex"}
				flexWrap={"nowrap"}
				justifyContent={"space-between"}
				alignItems={"center"}
			>
				{/** <img src={HeaderImage} alt={"Teracotta preview app"} /> */}
			</Box>
			{host && keys && (
				<Box my={1} mt={2}>
					<Typography variant={"body1"} sx={styles.hostText}>
						<b>Host: </b>
						<span>{host}</span>
					</Typography>
					<Typography variant={"body1"} sx={styles.hostText}>
						<b>Docs: </b>
						<Link href={`${host}/apidoc`} target={"_blank"}>
							<span>{`${host}/apidoc`}</span>
						</Link>
					</Typography>
					<Typography variant={"body1"} sx={styles.hostText}>
						<b>{"Keys: "}</b>
						<span>
							{keys.map((keyItem: KeyItem) =>
								keyItem.description ? (
									<Tooltip
										title={keyItem.description || false}
										key={`tooltip-${keyItem.key}`}
									>
										<Typography>
											{"/"}
											<Typography
												sx={styles.hasDescription}
											>{`{${keyItem.key.toLowerCase()}}`}</Typography>
										</Typography>
									</Tooltip>
								) : (
									<Typography key={`tooltip-${keyItem.key}`}>
										{"/"}
										<Typography
											sx={styles.noDescription}
										>{`{${keyItem.key.toLowerCase()}}`}</Typography>
									</Typography>
								),
							)}
						</span>
					</Typography>
				</Box>
			)}
		</Box>
	);
};

export default SidebarTitle;
