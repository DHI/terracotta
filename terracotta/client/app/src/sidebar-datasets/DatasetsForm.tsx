import React, { FC, useState, useEffect, FormEvent } from 'react'
import { Box, TextField, Button, Grid } from '@mui/material'
import { KeyItem } from '../common/data/getData'

type FormValues = Record<string, string | number> | undefined

interface Props {
	keys: KeyItem[]
	onSubmitFields: (queryString: string) => void
}
const DatasetsForm: FC<Props> = ({ keys, onSubmitFields }) => {
	const [formValues, setFormValues] = useState<FormValues>(undefined)

	const onSubmitForm = (e: FormEvent<HTMLFormElement> | undefined) => {
		if (e) {
			e.preventDefault()
		}
		if (formValues) {
			const queryString = Object.keys(formValues)
				.map((keyItem: string) =>
					formValues[keyItem] !== ''
						? `&${keyItem}=${formValues[keyItem]}`
						: '',
				)
				.join('')

			if (queryString) {
				onSubmitFields(queryString)
			}
		}
	}

	useEffect(() => {
		const reduceKeys = keys.reduce(
			(acc: Record<string, string>, keyItem: KeyItem) => {
				acc[keyItem.key.toLowerCase()] = ''
				return acc
			},
			{},
		)

		setFormValues(reduceKeys)
	}, []) // eslint-disable-line react-hooks/exhaustive-deps

	return (
		<>
			<Grid direction="row" spacing={1} width="100%" container>
				{keys.map((keyItem: KeyItem) => (
					<Grid key={keyItem.key} xs={6} item>
						<TextField
							id={keyItem.key.toLocaleLowerCase()}
							label={keyItem.key}
							size="small"
							value={formValues?.[keyItem.key]}
							fullWidth
							onChange={(e) =>
								setFormValues((val) => ({
									...val,
									[keyItem.key.toLocaleLowerCase()]: e.target.value,
								}))
							}
						/>
					</Grid>
				))}
			</Grid>
			<Box display="flex" justifyContent="flex-end" mt={2} width={1}>
				<Button
					type="submit"
					variant="contained"
					fullWidth
					onClick={() => onSubmitForm(undefined)}
				>
					Search
				</Button>
			</Box>
		</>
	)
}

export default DatasetsForm
