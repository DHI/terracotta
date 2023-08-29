import React, { FC, useState, useEffect, FormEvent } from 'react'
import { Box, TextField, Button } from '@mui/material'
import { makeStyles } from '@mui/material/styles'
import { KeyItem } from '../common/data/getData'

type FormValues = Record<string, string | number> | undefined

const styles = {
	input: {
		width: '50%',
	},
	inputLabel: {
		'& label': {
			fontSize: 12,
		},
	},
}

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
	}, [])

	return (
		<form onSubmit={(e) => onSubmitForm(e)}>
			{keys.map((keyItem: KeyItem, i: number) => {
				const isLastUneven = !!(keys.length % 2 === 1 && i === keys.length - 1)
				return (
					<TextField
						fullWidth={isLastUneven}
						id={keyItem.key.toLocaleLowerCase()}
						key={`textfield-${keyItem.key}`}
						label={keyItem.key}
						sx={isLastUneven ? {} : { ...styles.input, ...styles.inputLabel }}
						value={formValues?.[keyItem.key]}
						onChange={(e) =>
							setFormValues((val) => ({
								...val,
								[keyItem.key.toLowerCase()]: e.target.value,
							}))
						}
					/>
				)
			})}
			<Box display="flex" justifyContent="flex-end" mt={2} width={1}>
				<Button
					color="secondary"
					type="submit"
					variant="contained"
					fullWidth
					onClick={() => onSubmitForm(undefined)}
				>
					Search
				</Button>
			</Box>
		</form>
	)
}

export default DatasetsForm
