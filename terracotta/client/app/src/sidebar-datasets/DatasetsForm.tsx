import React, { FC, useState, useEffect, FormEvent } from 'react'
import { Box, TextField, Button  } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { KeyItem } from "../common/data/getData"

type FormValues = Record<string, string | number> | undefined

const useStyles = makeStyles(theme => ({
    input: {
        width: '50%'
    },
    inputLabel: {
        '& label': {
            fontSize: 12
        }
    }
}))

interface Props {
    keys: KeyItem[],
    onSubmitFields: (queryString: string) => void
}
const DatasetsForm: FC<Props> = ({
    keys,
    onSubmitFields
}) => {

    const classes = useStyles()
    const [ formValues, setFormValues ] = useState<FormValues>(undefined)

    const onSubmitForm = (e: FormEvent<HTMLFormElement> | undefined) => {
        if(e) e.preventDefault()
        if(formValues){

            const queryString = Object.keys(formValues).map(
                (keyItem: string) => 
                    formValues[keyItem] !== '' ? `&${keyItem}=${formValues[keyItem]}` : ''
                ).join('')

            if(queryString) onSubmitFields(queryString)
        }
    }

    useEffect(() => {
        const reduceKeys = keys.reduce((acc:Record<string, string> , keyItem: KeyItem) => {
           
            acc[keyItem.key.toLowerCase()] = ''
            return acc

        }, {})

        setFormValues(reduceKeys)

    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    return (
        <form onSubmit={e => onSubmitForm(e)}>
            {
                keys.map((keyItem: KeyItem, i: number) => {
                    const isLastUneven = keys.length % 2 === 1 && i === keys.length - 1 ? true : false
                return(
                    <TextField 
                        key={`textfield-${keyItem.key}`} 
                        id={keyItem.key.toLocaleLowerCase()} 
                        label={keyItem.key}
                        className={`${isLastUneven ? '' : classes.input} ${classes.inputLabel}`} 
                        fullWidth={isLastUneven}
                        onChange={(e) => setFormValues((val) => ({ ...val, [keyItem.key.toLowerCase()]: e.target.value }))}
                        value={formValues?.[ keyItem.key ]}
                    />
                )})
            }
            <Box mt={2} width={1} display={'flex'} justifyContent={'flex-end'}>
                <Button fullWidth type={'submit'} color={'secondary'} variant={'contained'} onClick={() => onSubmitForm(undefined)}>
                    {'Search'}
                </Button>
            </Box>
        </form>
    )

}

export default DatasetsForm
