import React, { FC } from 'react'
import {
	Box,
	TableRow,
	TableCell,
	Grid,
	Collapse,
	Typography,
	Link,
	Stack,
} from '@mui/material'
import { makeStyles } from '@mui/material/styles'
import { KeyItem, ResponseMetadata200 } from '../common/data/getData'
import CopyToClipboard from '../common/components/CopyToClipboard'

const styles = {
	imagePreview: {
		height: '90%',
		width: 'auto',
	},
	codeContainer: {
		backgroundColor: '#F8F8F8',
		overflowX: 'auto',
		width: 'fit-content',
		maxWidth: '100%',
	},
	codeContainerText: {
		color: '#557A8F',
	},
	copyTooltip: {
		cursor: 'pointer',
	},
	tableCell: {
		padding: 0,
	},
	metadataLink: {
		color: '#86A2B3',
	},
}

interface Props {
	keys: KeyItem[]
	host: string
	page: number
	limit: number
	i: number
	activeDataset?: number
	dataset: ResponseMetadata200
	datasetUrl?: string
}

const DatasetPreview: FC<Props> = ({
	keys,
	host,
	page,
	limit,
	i,
	activeDataset,
	dataset,
	datasetUrl,
}) => {
	const returnJson = JSON.stringify(
		{
			mean: dataset.mean,
			range: dataset.range,
			stdev: dataset.stdev,
			valid_percentage: dataset.valid_percentage,
		},
		null,
		2,
	)

	return (
		<TableRow
			sx={{
				display: page * limit + i === activeDataset ? 'table-row' : 'none',
			}}
		>
			<TableCell colSpan={8} sx={styles.tableCell}>
				<Collapse
					in={page * limit + i === activeDataset}
					timeout="auto"
					unmountOnExit
				>
					{datasetUrl && (
						<Box p={1} sx={styles.codeContainer}>
							<Stack alignItems="center" direction="row" gap={1} width={1}>
								<Typography sx={styles.codeContainerText}>
									<code>{'Raster url\n'}</code>
								</Typography>

								<CopyToClipboard
									helperText="Copy to clipboard"
									message={datasetUrl}
									url
								/>
							</Stack>
							<code style={{ wordBreak: 'break-all' }}>{datasetUrl}</code>
						</Box>
					)}
					<Box my={1}>
						<Grid alignItems="center" container>
							<Grid xs={6} item>
								<Box p={1} sx={styles.codeContainer}>
									<Typography sx={styles.codeContainerText}>
										<code>Metadata</code>
									</Typography>
									<code style={{ whiteSpace: 'pre' }}>{`${returnJson}\n`}</code>
									<Link
										href={`${host}/metadata${keys
											.map((keyItem) => `/${dataset.keys[keyItem.original]}`)
											.join('')}`}
										sx={styles.metadataLink}
										target="_blank"
									>
										{'View full metadata\n'}
									</Link>
								</Box>
							</Grid>
							<Grid
								alignItems="center"
								justifyContent="center"
								xs={6}
								container
								item
							>
								<Box p={1}>
									<Box
										alt="TC-preview"
										component="img"
										loading="eager"
										src={`${host}/singleband/${keys
											.map((key) => `${dataset.keys[key.original]}/`)
											.join('')}preview.png?tile_size=[128,128]`}
										sx={styles.imagePreview}
									/>
								</Box>
							</Grid>
						</Grid>
					</Box>
				</Collapse>
			</TableCell>
		</TableRow>
	)
}

export default DatasetPreview
