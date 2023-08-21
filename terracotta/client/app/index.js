const fs = require('fs');
const packageJson = require('./package.json');

['dependencies', 'devDependencies'].forEach(depType => {
    if (packageJson[depType]) {
        Object.keys(packageJson[depType]).forEach(pkg => {
            const installedPkg = require(`./node_modules/${pkg}/package.json`);
            packageJson[depType][pkg] = "^" + installedPkg.version;
        });
    }
});

fs.writeFileSync('./package.json', JSON.stringify(packageJson, null, '\t') + '\n')