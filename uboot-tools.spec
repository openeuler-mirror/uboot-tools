%global _default_patch_fuzz 2
%global with_armv8 1

Name:           uboot-tools
Version:        2021.10
Release:        7
Summary:        tools for U-Boot
License:        GPL-2.0-or-later and Public Domain and GPL-2.0-only
URL:            http://www.denx.de/wiki/U-Boot
Source0:        https://ftp.denx.de/pub/u-boot/u-boot-%{version}.tar.bz2
Source1:        arm-boards
Source2:        arm-chromebooks
Source3:        aarch64-boards
Source4:        aarch64-chromebooks
Source5:        10-devicetree.install

Patch6000:      backport-uefi-distro-load-FDT-from-any-partition-on-boot-device.patch
# RPi4llWinner improvements
Patch6001:      backport-AllWinner-PineTab.patch
# RPI4
Patch6002:      backport-rpi-Enable-using-the-DT-provided-by-the-Raspberry-Pi.patch
Patch6003:	backport-CVE-2022-34835.patch
Patch6004:      backport-CVE-2022-33967.patch
Patch6005:	backport-CVE-2022-30767.patch

BuildRequires:  bc dtc gcc make flex bison git-core openssl-devel
BuildRequires:  python3-unversioned-command python3-devel python3-setuptools
BuildRequires:  python3-libfdt python3-pyelftools SDL-devel swig
BuildRequires:  perl
# this required when /usr/bin/python link to python3
BuildRequires:  python3-devel
%if %{with_armv8}
%ifarch %{arm}  aarch64
BuildRequires:  vboot-utils
%endif
%ifarch aarch64
BuildRequires:  arm-trusted-firmware-armv8
%endif
%endif

Requires:       dtc systemd

%description
This package includes the mkimage program, which allows generation of U-Boot
images in various formats, and the fw_printenv and fw_setenv programs to read
and modify U-Boot's environment.

%if %{with_armv8}
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
Obsoletes:   	uboot-images-qemu < %{version}-%{release}
Provides:    	uboot-images-qemu = %{version}-%{release}

%description 	-n uboot-images-elf
u-boot bootloader ELF images for use with qemu and other platforms
%endif
%endif

%package_help

%prep
%autosetup -p1 -n u-boot-%{version}

cp %SOURCE1 %SOURCE2 %SOURCE3 %SOURCE4 .

%build
mkdir builds

%if %{with_armv8}
%ifarch aarch64 %{arm}
for board in $(cat %{_arch}-boards)
do
  echo "Building board: $board"
  if [[ " ${rk3399[*]} " == *" $board "* ]]; then
    echo "Board: $board  skipping"
    continue
  fi

  mkdir builds/$(echo $board)/
  sun50i=(a64-olinuxino amarula_a64_relic bananapi_m2_plus_h5  bananapi_m64 libretech_all_h3_cc_h5 nanopi_neo2 nanopi_neo_plus2 orangepi_pc2 orangepi_prime orangepi_win orangepi_zero_plus orangepi_zero_plus2 pine64-lts pine64_plus pinebook pinephone pinetab sopine_baseboard teres_i)
  if [[ " ${sun50i[*]} " == *" $board "* ]]; then
    echo "Board: $board using sun50i_a64"
    cp /usr/share/arm-trusted-firmware/sun50i_a64/* builds/$(echo $board)/
  fi
  sun50h6=(orangepi_lite2 orangepi_one_plus pine_h64)
  if [[ " ${sun50h6[*]} " == *" $board "* ]]; then
    echo "Board: $board using sun50i_h6"
    cp /usr/share/arm-trusted-firmware/sun50i_h6/* builds/$(echo $board)/
  fi
    rk3328=(evb-rk3328 rock64-rk3328)
  if [[ " ${rk3328[*]} " == *" $board "* ]]; then
    echo "Board: $board using rk3328"
    cp /usr/share/arm-trusted-firmware/rk3328/* builds/$(echo $board)/
  fi
  rk3399=(evb-rk3399 ficus-rk3399 khadas-edge-captain-rk3399 khadas-edge-v-rk3399 khadas-edge-rk3399 nanopc-t4-rk3399 nanopi-m4-rk3399 nanopi-neo4-rk3399 orangepi-rk3399 pinebook-pro-rk3399 puma-rk3399 rock960-rk3399 rock-pi-4-rk3399 rockpro64-rk3399 roc-pc-rk3399)
  if [[ " ${rk3399[*]} " == *" $board "* ]]; then
    echo "Board: $board using rk3399"
    cp /usr/share/arm-trusted-firmware/rk3399/* builds/$(echo $board)/
  fi
  # End ATF
  make $(echo $board)_defconfig O=builds/$(echo $board)/
  make HOSTCC="gcc $RPM_OPT_FLAGS" CROSS_COMPILE="" %{?_smp_mflags} V=1 O=builds/$(echo $board)/
done
%endif
%endif

make HOSTCC="gcc $RPM_OPT_FLAGS" %{?_smp_mflags} CROSS_COMPILE="" defconfig V=1 O=builds/ -j16
make HOSTCC="gcc $RPM_OPT_FLAGS" %{?_smp_mflags} CROSS_COMPILE="" tools-all V=1 O=builds/ -j16

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_sysconfdir}
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_datadir}/uboot/

%if %{with_armv8}
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
%endif

for tool in bmp_logo dumpimage env/fw_printenv fit_check_sign fit_info gdb/gdbcont gdb/gdbsend gen_eth_addr gen_ethaddr_crc img2srec mkenvimage mkimage mksunxiboot ncb proftool sunxi-spl-image-builder ubsha1 xway-swap-bytes
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

%if %{with_armv8}
%ifarch aarch64
%files -n uboot-images-armv8
%defattr(-,root,root)
%{_datadir}/uboot/*
%endif

%ifarch %{arm}
%files -n uboot-images-armv7
%defattr(-,root,root)
%{_datadir}/uboot/*
%endif

%ifarch %{arm} aarch64
%files -n uboot-images-elf
%defattr(-,root,root)
%endif
%endif

%files help
%doc README doc/README.kwbimage doc/README.distro doc/README.gpt
%doc doc/README.odroid doc/README.rockchip doc/uImage.FIT
%doc builds/docs/* doc/arch/arm64.rst
%doc doc/board/amlogic/ doc/board/rockchip/
%{_mandir}/man1/mkimage.1*

%changelog
* Wed Sep 28 2022 zhouwenpei <zhouwenpei1@h-partners.com> - 2021.10-7
- fix CVE-2022-30767

* Wed Jul 20 2022 cenhuilin <cenhuilin@kylinos.cn> - 2021.10-6
- fix CVE-2022-33967

* Tue Jul 12 2022 zhouwenpei <zhouwenpei1@h-partners.com> - 2021.10-5
- fix CVE-2022-34835

* Wed May 11 2022 liuyumeng <liuyumeng5@h-partners.com> - 2021.10-4
- fix license error

* Sat May 07 2022 liuyumeng <liuyumeng5@h-partners.com> - 2021.10-3
- fix license error

* Wed Apr 13 2022 yangcheng <yangcheng87@h-partners.com> - 2021.10-2
- Add perl buildrequires to resolve compilation error

* Mon Dec 6 2021 yangcheng <yangcheng87@huawei.com> - 2021.10-1
- Upgrade to 2021.10

* Wed Jul 21 2021 yushaogui <yushaogui@huawei.com> - 2020.07-7
- Delete a Buildrequires for gdb

* Mon Apr 19 2021 liuyumeng <liuyumeng@huawei.com> - 2020.07-6
- Compilation optimzation

* Tue Mar 16 2021 yanglu <yanglu@60huawei.com> - 2020.07-5
- Type:cves
- ID:CVE-2021-27097 CVE-2021-27138
- SUG:NA
- DESC:fix CVE-2021-27097CVE-2021-27138

* Wed Dec 16 2020 zhanzhimin <zhanzhimin@huawei.com> - 2020.07-4
- Update Source0

* Wed Oct 21 2020 jinzhimin <jinzhimin2@huawei.com> - 2020.07-3
- modify buildrequire to python3-unversioned-command 

* Tue Sep 10 2020 chengguipeng<chengguipeng1@huawei.com> - 2020.07-2
- Type:bugfix
- ID:NA
- SUG:NA
- DESC:modify source0 url

* Fri Jul 31 2020 chengguipeng<chengguipeng1@huawei.com> 2020.07-1
- Upgrade to 2020.07-1

* Fri Jun 19 2020 zhujunhao <zhujunhao8@huawei.com> - 2018.09-9
- drop python2 requires

* Fri Mar 20 2020 songnannan <songnannan2@huawei.com> - 2018.09-8
- add gdb in buildrequires

* Sat Feb 29 2020 hexiujun <hexiujun1@huawei.com> - 2018.09-7
- Type:enhancement
- ID:NA
- SUG:NA
- DESC: compatible with python3 compile environment

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
