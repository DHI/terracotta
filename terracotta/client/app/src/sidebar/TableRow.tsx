import React, { FC } from 'react'
import { TableRow as MuiTableRow, TableCell, Box, IconButton } from '@material-ui/core'
import { makeStyles } from "@material-ui/core/styles"
import { DatasetItem } from "../common/data/getData"
import RadioButtonUncheckedIcon from '@material-ui/icons/RadioButtonUnchecked';
import CheckCircleIcon from '@material-ui/icons/CheckCircle';

const useStyles = makeStyles(() => ({
    tableCell: {
        padding: 6,
        borderBottom: 'none'
    },
    tableRow: {
        cursor: 'pointer'
    },
    icon: {
        width: 18,
        height: 18
    },
    iconChecked: {
        color: '#61C051',
    },
    noPadding: {
        padding: 0
    }
}))

interface Props {
    dataset: DatasetItem,
    keyVal: string,
    checked: boolean,
    onClick?: () => void,
    onMouseEnter?: () => void,
    onMouseLeave?: () => void
}

const TableRow: FC<Props> = ({ 
    dataset, 
    keyVal, 
    checked, 
    onClick,
    onMouseEnter,
    onMouseLeave 
}) => {

    const classes = useStyles()
    
    return (
            <MuiTableRow 
                hover 
                onClick={onClick} 
                className={classes.tableRow}
                onMouseEnter={onMouseEnter}
                onMouseLeave={onMouseLeave}
            >
                <TableCell className={classes.tableCell} >
                    <Box display={'flex'} alignItems={'center'}>
                        {
                            checked ? 
                            <IconButton classes={{root: classes.noPadding}}>
                                <CheckCircleIcon className={`${classes.iconChecked} ${classes.icon}`}/>
                            </IconButton> : 
                            <IconButton classes={{root: classes.noPadding}}>
                                <RadioButtonUncheckedIcon className={classes.icon}/>
                            </IconButton>
                        }
                    </Box>
                </TableCell>
                {
                    Object.keys(dataset).map((item: string, i: number) => (
                        <TableCell className={classes.tableCell} key={`${keyVal}-cell-${i}`}>
                            {dataset[item]}
                        </TableCell>
                    ))
                }
            </MuiTableRow>
    )
}

export default TableRow
