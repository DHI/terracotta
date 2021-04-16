import React, { FC, useState, useEffect, ChangeEvent } from 'react'
import { Box, TextField, Button  } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

type FormValues = Record<string, string | number> | undefined
type OnChangeInput = ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
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
    keys: string[],
    onSubmitFields: (queryString: string) => void
}
const DatasetsForm: FC<Props> = ({
    keys,
    onSubmitFields
}) => {

    const classes = useStyles()
    const [ formValues, setFormValues ] = useState<FormValues>(undefined)
    const onChangeInput = (e: OnChangeInput, inputKey: string) => {
        inputKey = inputKey.toLowerCase()
        if(formValues){
            const formValuesCopy = formValues
            formValuesCopy[inputKey] = e.target.value
            setFormValues(formValuesCopy)
        }
    }

    const onSubmitForm = () => {
        console.log(formValues)
        if(formValues){

            const queryString = Object.keys(formValues).map(
                (keyItem: string) => 
                    formValues[keyItem] !== '' ? `&${keyItem}=${formValues[keyItem]}` : ''
                ).join('')

            if(queryString) onSubmitFields(queryString)
        }
    }

    useEffect(() => {

        const reduceKeys = keys.reduce((acc:Record<string, string> , keyItem: string) => {
           
            acc[keyItem.toLowerCase()] = ''
            return acc

        }, {})

        setFormValues(reduceKeys)

    }, [keys])

    return (
        <Box>
            {
                keys.map((keyItem: string, i: number) => {
                    const isLastUneven = keys.length % 2 === 1 && i === keys.length - 1 ? true : false
                return(
                    <TextField 
                        key={`textfield-${keyItem}`} 
                        id={keyItem.toLocaleLowerCase()} 
                        label={keyItem}
                        className={`${isLastUneven ? '' : classes.input} ${classes.inputLabel}`} 
                        fullWidth={isLastUneven}
                        onChange={(e) => onChangeInput(e, keyItem.toLowerCase())}
                    />
                )})
            }
            <Box mt={2} width={1} display={'flex'} justifyContent={'flex-end'}>
                <Button fullWidth type={'button'} color={'secondary'} variant={'contained'} onClick={onSubmitForm}>
                    {'Search'}
                </Button>
            </Box>
        </Box>
    )

}

export default DatasetsForm
