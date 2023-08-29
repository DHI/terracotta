import { TypographyVariantsOptions, Palette } from '@mui/material/styles'

const FONT_FAMILY = [
	'Roboto',
	'-apple-system',
	'BlinkMacSystemFont',
	'Arial',
	'sans-serif',
].join(',')

const dhiTypography:
	| TypographyVariantsOptions
	| ((palette: Palette) => TypographyVariantsOptions) = {
	htmlFontSize: 16,
	fontSize: 14,
	fontFamily: FONT_FAMILY,
	h1: {
		fontSize: '2rem', // 32px
		lineHeight: 1.25, // 40px - default mui:1
		fontWeight: 'normal',
	},
	h2: {
		fontSize: '1.5rem', // 24px
		lineHeight: 1.33, // 32px  - default mui:1
		fontWeight: 'normal',
	},
	h3: {
		fontSize: '1.25rem', // 20px
		lineHeight: 1.2, // 24px  - default mui:1.04
		fontWeight: 'bold',
	},
	h4: {
		fontSize: '1rem', // 16px
		lineHeight: 1.25, // 20px  - default mui:1.17
		fontWeight: 'bold',
	},
	h5: {
		// not defined in DHI guidelines
		fontSize: '1rem', // 16px
		lineHeight: 1, // 16px  - default mui:1.33
		fontWeight: 'bold',
	},
	h6: {
		// Used by mui for DialogTitles
		fontSize: '1.25rem', // 20 px
		lineHeight: 1.2, // 24px  - default mui:1.6
		fontWeight: 'bold',
	},
	subtitle1: {}, // default mui: 1rem / 1.75
	subtitle2: {}, // default mui: 0.875rem / 1.57
	body1: {
		// In Figma: Body Text
		// default mui: 1rem / 1.5.
		fontSize: '1rem', // 16px
		lineHeight: 1.374, // 22px
	},
	body2: {
		// In Figma: Body Text (S)
		// default mui: 0.875rem / 1.43
		fontSize: '0.875rem', // 14px
		lineHeight: 1.286, // 18px
	},
	button: {}, // default mui: 0.875rem / 1.75 / UPPERCASE
	caption: {}, // default mui: 0.75rem / 1.66
	overline: {}, // default mui: 0.75rem / 2.66 / UPPERCASE
}

export default dhiTypography
