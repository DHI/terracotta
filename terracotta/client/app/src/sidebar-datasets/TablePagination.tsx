import React, { FC, ChangeEvent } from 'react'
import { 
    Box,
    FormControl,
    MenuItem,
    Select,
    IconButton,
    Typography
 } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import NavigateBeforeIcon from '@material-ui/icons/NavigateBefore';

const useStyles = makeStyles(() => ({
    formControl: {
        border: 'none',
        marginLeft: 6
    },
    icon: {
        width: 20,
        height: 20,
        cursor: 'pointer'
    }
}))

interface Props {
    value: number,
    options: number[],
    onGetValue: (val: number) => void,
    page: number,
    onGetPage: (page: number) => void,
    disableNext: boolean
}
const TablePagination: FC<Props> = ({
    value, 
    options, 
    onGetValue,
    onGetPage,
    page,
    disableNext
}) => {
    const classes = useStyles()

    const handleChange = (e: ChangeEvent<{ name?: string | undefined; value: unknown; }>) => {
        onGetValue(Number(e.target.value))
    }

    const onNextPage = () => {
        onGetPage(page + 1)
    }

    const onPreviousPage = () => {
        onGetPage(page - 1)
    }

    return (
        <Box display={'flex'} justifyContent={'space-between'} alignItems={'center'}>
             <Box display={'flex'} alignItems={'center'}>
                <IconButton disabled={page === 0} onClick={onPreviousPage}>
                    <NavigateBeforeIcon className={classes.icon}/>
                </IconButton>
                <Typography variant={'body2'}>
                    {`Page ${page}`}
                </Typography>
                <IconButton onClick={onNextPage} disabled={disableNext}>
                    <NavigateNextIcon className={classes.icon}/>
                </IconButton>
            </Box>
            <Box display={'flex'} alignItems={'center'}>
                <Typography variant={'body2'}>
                    {'Rows per page:'}
                </Typography>
                <FormControl className={classes.formControl}>
                    <Select
                        id="demo-simple-select-outlined"
                        value={value}
                        onChange={handleChange}
                    >
                        {
                            options.map((option: number, i: number) => (
                                <MenuItem key={`limit-${option}`} value={option}>{option}</MenuItem>
                            ))
                        }
                    </Select>
                </FormControl>
            </Box>
        </Box>
    )
}

export default TablePagination
