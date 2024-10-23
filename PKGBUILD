# Maintainer: Jasur Sadikov <jasur@sadikoff.com>
pkgname=mud
pkgver=v1.0.2
pkgrel=1
pkgdesc="Multi repository git utility. Manage multiple git-repositories simultaneously."
arch=('any')
url="https://github.com/jasursadikov/mud"
license=('MIT')
depends=('python' 'python-prettytable')
makedepends=('python-build' 'python-installer' 'git')
source=("${_pkgname}::git+https://github.com/jasursadikov/mud.git")
md5sums=('SKIP')

pkgver() {
    cd "$srcdir/$_pkgname"
    echo $(grep '^version =' pyproject.toml | cut -d '"' -f2)
}

build() {
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$_pkgname"
    python -m installer --destdir="$pkgdir" dist/*.whl
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
