export interface Colormap {
    displayName: string,
    id: string,
    img_url: string
}

const COLORMAPS: Colormap[] = [
    { 
        displayName: 'Greys', 
        id: 'greys', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-greys-bar.png' 
    },
    { 
        displayName: 'Gray', 
        id: 'gray', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gray-bar.png' 
    },
    { 
        displayName: 'Binary', 
        id: 'binary', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-binary-bar.png' 
    },
    { 
        displayName: 'Bone', 
        id: 'bone', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-bone-bar.png'
    },
    { 
        displayName: 'Cloud', 
        id: 'cloud', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-cloud-bar.png' 
    },
    { 
        displayName: 'Blues', 
        id: 'blues', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-blues-bar.png'
    },
    { 
        displayName: 'Viridis', 
        id: 'viridis', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-viridis-bar.png' 
    },
    { 
        displayName: 'Cividis', 
        id: 'cividis', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-cividis-bar.png' 
    },
    { 
        displayName: 'Magma', 
        id: 'magma', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-magma-bar.png' 
    },
    { 
        displayName: 'Ocean', 
        id: 'ocean', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-ocean-bar.png' 
    },
    { 
        displayName: 'Afmhot', 
        id: 'afmhot', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-afmhot-bar.png' 
    },
    { 
        displayName: 'Hot', 
        id: 'hot', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-hot-bar.png' 
    },
    { 
        displayName: 'Inferno', 
        id: 'inferno', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-inferno-bar.png' 
    },
    { 
        displayName: 'Plasma', 
        id: 'plasma', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-plasma-bar.png' 
    },
    { 
        displayName: 'Spring', 
        id: 'spring', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-spring-bar.png' 
    },
    { 
        displayName: 'Summer', 
        id: 'summer', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-summer-bar.png' 
    },
    { 
        displayName: 'Autumn', 
        id: 'autumn', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-autumn-bar.png' 
    },
    { 
        displayName: 'Winter', 
        id: 'winter', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-winter-bar.png' 
    },
    { 
        displayName: 'Wistia', 
        id: 'wistia', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-wistia-bar.png' 
    },
    { 
        displayName: 'Terrain', 
        id: 'terrain', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-terrain-bar.png' 
    },
    { 
        displayName: 'Twilight', 
        id: 'twilight', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-twilight-bar.png' 
    },
    { 
        displayName: 'Twilight_shifted', 
        id: 'twilight_shifted', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-twilight_shifted-bar.png' 
    },
    { 
        displayName: 'Ylgn', 
        id: 'ylgn', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-ylgn-bar.png' 
    },
    { 
        displayName: 'Brbg', 
        id: 'brbg', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-brbg-bar.png' 
    },
    { 
        displayName: 'Brg', 
        id: 'brg', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-brg-bar.png' 
    },
    { 
        displayName: 'Bugn', 
        id: 'bugn', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-bugn-bar.png' 
    },
    { 
        displayName: 'Bupu', 
        id: 'bupu', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-bupu-bar.png' 
    },
    { 
        displayName: 'Bwr', 
        id: 'bwr', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-bwr-bar.png' 
    },
    { 
        displayName: 'Gnbu',
        id: 'gnbu', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gnbu-bar.png' 
    },
    { 
        displayName: 'Orrd', 
        id: 'orrd', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-orrd-bar.png' 
    },
    { 
        displayName: 'Piyg', 
        id: 'piyg', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-piyg-bar.png' 
    },
    { 
        displayName: 'Prgn', 
        id: 'prgn', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-prgn-bar.png' 
    },
    { 
        displayName: 'Pubu', 
        id: 'pubu', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-pubu-bar.png' 
    },
    { 
        displayName: 'Puor', 
        id: 'puor', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-puor-bar.png' 
    },
    {
        displayName: 'Purd', 
        id: 'purd', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-purd-bar.png' 
    },
    { 
        displayName: 'Pubugn', 
        id: 'pubugn', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-pubugn-bar.png' 
    },
    { 
        displayName: 'Rdbu', 
        id: 'rdbu', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-rdbu-bar.png' 
    },
    { 
        displayName: 'Rdgy', 
        id: 'rdgy', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-rdgy-bar.png' 
    },
    { 
        displayName: 'Rdpu', 
        id: 'rdpu', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-rdpu-bar.png' 
    },
    { 
        displayName: 'Rdylbu', 
        id: 'rdylbu', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-rdylbu-bar.png' 
    },
    { 
        displayName: 'Ylgnbu', 
        id: 'ylgnbu', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-ylgnbu-bar.png' 
    },
    { 
        displayName: 'Ylorbr', 
        id: 'ylorbr', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-ylorbr-bar.png' 
    },
    { 
        displayName: 'Ylorrd', 
        id: 'ylorrd', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-ylorrd-bar.png' 
    },
    { 
        displayName: 'Rdylgn', 
        id: 'rdylgn', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-rdylgn-bar.png' 
    },
    { 
        displayName: 'Greens', 
        id: 'greens', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-greens-bar.png' 
    },
    { 
        displayName: 'Pink', 
        id: 'pink', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-pink-bar.png' 
    },
    { 
        displayName: 'Oranges', 
        id: 'oranges', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-oranges-bar.png' 
    },
    { 
        displayName: 'Purples', 
        id: 'purples', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-purples-bar.png' 
    },
    { 
        displayName: 'Reds', 
        id: 'reds', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-reds-bar.png' 
    },
    { 
        displayName: 'Rainbow', 
        id: 'rainbow', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-rainbow-bar.png' 
    },
    { 
        displayName: 'Gnuplot', 
        id: 'gnuplot', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gnuplot-bar.png' 
    },
    { 
        displayName: 'Gnuplot2', 
        id: 'gnuplot2', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gnuplot2-bar.png' 
    },
    { 
        displayName: 'Cmrmap', 
        id: 'cmrmap', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-cmrmap-bar.png' 
    },
    { 
        displayName: 'Cool', 
        id: 'cool', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-cool-bar.png' 
    },
    { 
        displayName: 'Coolwarm', 
        id: 'coolwarm', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-coolwarm-bar.png' 
    },
    { 
        displayName: 'Copper', 
        id: 'copper', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-copper-bar.png' 
    },
    { 
        displayName: 'Cubehelix', 
        id: 'cubehelix', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-cubehelix-bar.png' 
    },
    { 
        displayName: 'Seismic', 
        id: 'seismic', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-seismic-bar.png' 
    },
    { 
        displayName: 'Accent', 
        id: 'accent', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-accent-bar.png' 
    },
    { 
        displayName: 'Dark2', 
        id: 'dark2', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-dark2-bar.png' 
    },
    { 
        displayName: 'Flag', 
        id: 'flag', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-flag-bar.png' 
    },
    { 
        displayName: 'Prism', 
        id: 'prism', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-prism-bar.png' 
    },
    { 
        displayName: 'Paired', 
        id: 'paired', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-paired-bar.png' 
    },
    { 
        displayName: 'Pastel1', 
        id: 'pastel1', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-pastel1-bar.png' 
    },
    { 
        displayName: 'Pastel2', 
        id: 'pastel2', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-pastel2-bar.png' 
    },
    { 
        displayName: 'Set1', 
        id: 'set1', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-set1-bar.png' 
    },
    { 
        displayName: 'Set2', 
        id: 'set2', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-set2-bar.png' 
    },
    { 
        displayName: 'Set3', 
        id: 'set3', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-set3-bar.png' 
    },
    { 
        displayName: 'Tab10', 
        id: 'tab10', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-tab10-bar.png' 
    },
    { 
        displayName: 'Tab20', 
        id: 'tab20', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-tab20-bar.png' 
    },
    { 
        displayName: 'Tab20b', 
        id: 'tab20b', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-tab20b-bar.png' 
    },
    { 
        displayName: 'Tab20c', 
        id: 'tab20c', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-tab20c-bar.png' 
    },
    { 
        displayName: 'Gist_earth', 
        id: 'gist_earth', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gist_earth-bar.png' 
    },
    { 
        displayName: 'Gist_heat', 
        id: 'gist_heat', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gist_heat-bar.png' 
    },
    { 
        displayName: 'Gist_ncar', 
        id: 'gist_ncar', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gist_ncar-bar.png' 
    },
    { 
        displayName: 'Gist_rainbow', 
        id: 'gist_rainbow', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gist_rainbow-bar.png' 
    },
    { 
        displayName: 'Gist_stern', 
        id: 'gist_stern', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gist_stern-bar.png' 
    },
    { 
        displayName: 'Gist_gray', 
        id: 'gist_gray', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gist_gray-bar.png' 
    },
    { 
        displayName: 'Gist_yarg', 
        id: 'gist_yarg', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-gist_yarg-bar.png' 
    },
    { 
        displayName: 'Hsv', 
        id: 'hsv', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-hsv-bar.png' 
    },
    { 
        displayName: 'Jet', 
        id: 'jet', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-jet-bar.png' 
    },
    { 
        displayName: 'Nipy_spectral', 
        id: 'nipy_spectral', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-nipy_spectral-bar.png'
    },
    { 
        displayName: 'Sepctral', 
        id: 'spectral', 
        img_url: 'https://terracotta-python.readthedocs.io/en/latest/_images/cmap-spectral-bar.png' 
    },
    
]

export default COLORMAPS;