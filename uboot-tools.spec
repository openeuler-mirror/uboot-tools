Name:           uboot-tools
Version:        2018.09
Release:        6
Summary:        tools for U-Boot
License:        GPLv2+ BSD LGPL-2.1+ LGPL-2.0+
URL:            http://www.denx.de/wiki/U-Boot
Source0:        ftp://ftp.denx.de/pub/u-boot/u-boot-%{version}%{?candidate:-%{candidate}}.tar.bz2
Source1:        arm-boards
Source2:        arm-chromebooks
Source3:        aarch64-boards
Source4:        aarch64-chromebooks
Source5:        10-devicetree.install
Patch0001:      usb-kbd-fixes.patch
Patch0002:      rpi-Enable-using-the-DT-provided-by-the-Raspberry-Pi.patch
Patch0003:      rockchip-make_fit_atf-fix-warning-unit_address_vs_reg.patch
Patch0004:      rockchip-make_fit_atf-use-elf-entry-point.patch
Patch0005:      rk3399-Rock960-board-support.patch
Patch0006:      dragonboard-fixes.patch
Patch0007:      tegra-efi_loader-simplify-ifdefs.patch
Patch0008:      sunxi-DT-A64-add-Pine64-LTS-support.patch

BuildRequires:  bc dtc gcc make flex bison git-core openssl-devel 
BuildRequires:  python-unversioned-command python2-devel python2-setuptools
BuildRequires:  python2-libfdt python2-pyelftools SDL-devel swig
%ifarch %{arm} aarch64
BuildRequires:  vboot-utils
%endif
%ifarch aarch64
BuildRequires:  arm-trusted-firmware-armv8
%endif

Requires:       dtc systemd

%description
This package includes the mkimage program, which allows generation of U-Boot
images in various formats, and the fw_printenv and fw_setenv programs to read
and modify U-Boot's environment.

%ifarch aarch64
%package     	-n uboot-images-armv8
Summary:     	u-boot bootloader images for aarch64 boards
Requires:    	uboot-tools
BuildArch:   	noarch

%description 	-n uboot-images-armv8
u-boot bootloader images for aarch64 boards
%endif

%ifarch %{arm}
%package     	-n uboot-images-armv7
Summary:     	u-boot bootloader images for armv7 boards
Requires:    	uboot-tools
BuildArch:   	noarch

%description 	-n uboot-images-armv7
u-boot bootloader images for armv7 boards
%endif

%ifarch %{arm} aarch64
%package     	-n uboot-images-elf
Summary:     	u-boot bootloader images for armv7 boards
Requires:    	uboot-tools
Obsoletes:   	uboot-images-qemu
Provides:    	uboot-images-qemu

%description 	-n uboot-images-elf
u-boot bootloader ELF images for use with qemu and other platforms
%endif

%package_help

%prep
%setup -q -n u-boot-%{version}

git init
git config --global gc.auto 0
git config user.email "noone@example.com" 
git config user.name "no one" 
git add . 
git commit -a -q -m "%{version} baseline" 
git am %{patches} </dev/null 
git config --unset user.email 
git config --unset user.name 
rm -rf .git

cp %SOURCE1 %SOURCE2 %SOURCE3 %SOURCE4 .

%build
mkdir builds

%ifarch aarch64 %{arm}
for board in $(cat %{_arch}-boards)
do
  echo "Building board: $board"
  if [[ " ${rk3399[*]} " == *" $board "* ]]; then
    echo "Board: $board  skipping"
    continue
  fi

  mkdir builds/$(echo $board)/
  sun50i=(a64-olinuxino bananapi_m64 libretech_all_h3_cc_h5 nanopi_neo2 nanopi_neo_plus2 orangepi_pc2 orangepi_prime orangepi_win orangepi_zero_plus orangepi_zero_plus2 pine64_plus sopine_baseboard)
  if [[ " ${sun50i[*]} " == *" $board "* ]]; then
    echo "Board: $board using sun50i_a64"
    cp /usr/share/arm-trusted-firmware/sun50i_a64/* builds/$(echo $board)/
  fi
  sun50i=(orangepi_one_plus pine_h64)
  if [[ " ${sun50i[*]} " == *" $board "* ]]; then
    echo "Board: $board using sun50i_h6"
    cp /usr/share/arm-trusted-firmware/sun50i_h6/* builds/$(echo $board)/
  fi
  rk3399=(evb-rk3399 firefly-rk3399 rock960-rk3399)
  if [[ " ${rk3399[*]} " == *" $board "* ]]; then
    echo "Board: $board using rk3399"
    cp /usr/share/arm-trusted-firmware/rk3399/* builds/$(echo $board)/
  fi
  make $(echo $board)_defconfig O=builds/$(echo $board)/
  make HOSTCC="gcc $RPM_OPT_FLAGS" CROSS_COMPILE="" %{?_smp_mflags} V=1 O=builds/$(echo $board)/
  rk33xx=(evb-rk3399)
  if [[ " ${rk33xx[*]} " == *" $board "* ]]; then
    echo "Board: $board using rk33xx"
    make HOSTCC="gcc $RPM_OPT_FLAGS" CROSS_COMPILE="" u-boot.itb V=1 O=builds/$(echo $board)/
    builds/$(echo $board)/tools/mkimage -n rk3399 -T rksd  -d builds/$(echo $board)/spl/u-boot-spl.bin builds/$(echo $board)/spl_sd.img
    builds/$(echo $board)/tools/mkimage -n rk3399 -T rkspi -d builds/$(echo $board)/spl/u-boot-spl.bin builds/$(echo $board)/spl_spi.img
  fi
done
%endif

make HOSTCC="gcc $RPM_OPT_FLAGS" %{?_smp_mflags} CROSS_COMPILE="" defconfig V=1 O=builds/
make HOSTCC="gcc $RPM_OPT_FLAGS" %{?_smp_mflags} CROSS_COMPILE="" tools-all V=1 O=builds/

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_sysconfdir}
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_datadir}/uboot/

%ifarch aarch64
for board in $(cat %{_arch}-boards)
do
mkdir -p %{buildroot}%{_datadir}/uboot/$(echo $board)/
 for file in spl/*spl.bin u-boot.bin u-boot.dtb u-boot-dtb.img u-boot.img u-boot.itb spl/sunxi-spl.bin
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -p -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/$(echo $board)/
  fi
 done
done
%endif

%ifarch %{arm}
for board in $(cat %{_arch}-boards)
do
mkdir -p %{buildroot}%{_datadir}/uboot/$(echo $board)/
 for file in MLO SPL spl/arndale-spl.bin spl/origen-spl.bin spl/smdkv310-spl.bin spl/*spl.bin u-boot.bin u-boot.dtb u-boot-dtb-tegra.bin u-boot.img u-boot.imx u-boot-nodtb-tegra.bin u-boot-spl.kwb u-boot-sunxi-with-spl.bin
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -p -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/$(echo $board)/
  fi
 done

done

for board in $(cat %{_arch}-boards)
do
  if [ -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot-sunxi-with-spl.bin ]; then
    rm -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot.*
  fi
  if [ -f %{buildroot}%{_datadir}/uboot/$(echo $board)/MLO ]; then
    rm -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot.bin
  fi
  if [ -f %{buildroot}%{_datadir}/uboot/$(echo $board)/SPL ]; then
    rm -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot.bin
  fi
  if [ -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot.imx ]; then
    rm -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot.bin
  fi
done
%endif

%ifarch aarch64
for board in $(cat %{_arch}-boards)
do
mkdir -p %{buildroot}%{_datadir}/uboot/$(echo $board)/
 for file in MLO SPL spl/arndale-spl.bin spl/origen-spl.bin spl/smdkv310-spl.bin u-boot.bin u-boot.dtb u-boot-dtb-tegra.bin u-boot.img u-boot.imx u-boot-nodtb-tegra.bin u-boot-spl.kwb u-boot-sunxi-with-spl.bin spl_sd.img spl_spi.img
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -p -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/$(echo $board)/
  fi
 done
done
%endif

%ifarch %{arm}
for board in vexpress_ca15_tc2 vexpress_ca9x4
do
mkdir -p %{buildroot}%{_datadir}/uboot/elf/$(echo $board)/
 for file in u-boot
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -p -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/elf/$(echo $board)/
  fi
 done
done
%endif

%ifarch aarch64
for board in $(cat %{_arch}-boards)
do
mkdir -p %{buildroot}%{_datadir}/uboot/elf/$(echo $board)/
 for file in u-boot
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -p -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/elf/$(echo $board)/
  fi
 done
done
%endif

for tool in bmp_logo dumpimage easylogo/easylogo env/fw_printenv fit_check_sign fit_info gdb/gdbcont gdb/gdbsend gen_eth_addr gen_ethaddr_crc img2srec mkenvimage mkimage mksunxiboot ncb proftool sunxi-spl-image-builder ubsha1 xway-swap-bytes
do
install -p -m 0755 builds/tools/$tool %{buildroot}%{_bindir}
done
install -p -m 0644 doc/mkimage.1 %{buildroot}%{_mandir}/man1

install -p -m 0755 builds/tools/env/fw_printenv %{buildroot}%{_bindir}
( cd %{buildroot}%{_bindir}; ln -sf fw_printenv fw_setenv )

install -p -m 0644 tools/env/fw_env.config %{buildroot}%{_sysconfdir}

mkdir -p %{buildroot}/lib/kernel/install.d/
install -p -m 0755 %{SOURCE5} %{buildroot}/lib/kernel/install.d/

mkdir -p builds/docs
cp -p board/amlogic/odroid-c2/README builds/docs/README.odroid-c2
cp -p board/hisilicon/hikey/README builds/docs/README.hikey
cp -p board/hisilicon/hikey/README builds/docs/README.hikey
cp -p board/Marvell/db-88f6820-gp/README builds/docs/README.mvebu-db-88f6820
cp -p board/rockchip/evb_rk3399/README builds/docs/README.evb_rk3399
cp -p board/solidrun/clearfog/README builds/docs/README.clearfog
cp -p board/solidrun/mx6cuboxi/README builds/docs/README.mx6cuboxi
cp -p board/sunxi/README.sunxi64 builds/docs/README.sunxi64
cp -p board/sunxi/README.nand builds/docs/README.sunxi-nand
cp -p board/ti/am335x/README builds/docs/README.am335x
cp -p board/ti/omap5_uevm/README builds/docs/README.omap5_uevm
cp -p board/udoo/README builds/docs/README.udoo
cp -p board/wandboard/README builds/docs/README.wandboard
cp -p board/warp/README builds/docs/README.warp
cp -p board/warp7/README builds/docs/README.warp7

%files
%defattr(-,root,root)
%doc README
%{_bindir}/*
/lib/kernel/install.d/10-devicetree.install
%dir %{_datadir}/uboot/
%config(noreplace) %{_sysconfdir}/fw_env.config

%ifarch aarch64
%files -n uboot-images-armv8
%defattr(-,root,root)
%{_datadir}/uboot/*
%exclude %{_datadir}/uboot/elf
%endif

%ifarch %{arm}
%files -n uboot-images-armv7
%defattr(-,root,root)
%{_datadir}/uboot/*
%exclude %{_datadir}/uboot/elf
%endif

%ifarch %{arm} aarch64
%files -n uboot-images-elf
%defattr(-,root,root)
%{_datadir}/uboot/elf/*
%endif

%files help
%defattr(-,root,root)
%doc doc/README.imximage doc/README.kwbimage doc/README.distro
%doc doc/README.gpt doc/README.odroid doc/README.rockchip doc/README.uefi
%doc doc/uImage.FIT doc/README.arm64 doc/README.chromium builds/docs/*
%{_mandir}/man1/mkimage.1.gz

%changelog
* Fri Jan 17 2020 Tianfei <tianfei16@huawei.com> - 2018.09-6
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: delete patch

* Tue Jan 14 2020 openEuler Buildteam <buildteam@openeuler.org> - 2018.09-5
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:close 3399

* Fri Oct 25 2019 openEuler Buildteam <buildteam@openeuler.org> - 2018.09-4
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:add the README files to the main package

* Sat Oct 12 2019 openEuler Buildteam <buildteam@openeuler.org> - 2018.09-3
- Package init

