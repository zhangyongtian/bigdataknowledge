---
sidebar_position: 5
sidebar_label: 升级gcc
---

## 下载网址

GCC的各个版本http://ftp.gnu.org/gnu/gcc/ ，根据自己需要选择，如果不知道，就选择最新的吧

## 下载GCC版本，这里选择最新的

假设下载文件放在/data/gcc目录

```
cd /data/gcc
wget http://ftp.gnu.org/gnu/gcc/gcc-11.2.0/gcc-11.2.0.tar.gz
```

解压

```
tar -zxvf gcc-11.2.0.tar.gz
```

下载各项依赖

```
cd gcc-11.2.0
./contrib/download_prerequisites
```

创建编译目录
还是在gcc-11.2.0目录

```
mkdir build
cd build
../configure --enable-checking=release --enable-languages=c,c++ --disable-multilib
```

编译
编译的过程可能需要几个小时，耐心等待

```
make
```

安装
编译完成后，执行安装

```
make install
```

检查gcc版本
如果版本还是旧的，执行reboot重启服务器，再查看

```
gcc -v
```

## 创建软链接

执行最开始的步骤，检查动态库是否正常

```
strings /usr/lib64/libstdc++.so.6 | grep GLIBC
```

如果还是没有GLIBCXX_3.4.21

查找GCC编译时生成的最新的动态库位置

```
find / -name "libstdc++.so*"
```

输出

```
/usr/lib/gcc/x86_64-redhat-linux/4.8.2/libstdc++.so
/usr/lib/gcc/x86_64-redhat-linux/4.8.2/32/libstdc++.so
/usr/lib/libstdc++.so.6
/usr/lib/libstdc++.so.6.0.19
/usr/local/qcloud/stargate/lib/libstdcxx-x86_64/libstdc++.so.6.0.20
/usr/local/qcloud/stargate/lib/libstdc++.so.6
/usr/local/qcloud/stargate/lib/libstdcxx-arm64/libstdc++.so.6.0.24
/usr/local/lib64/libstdc++.so.6
/usr/local/lib64/libstdc++.so.6.0.29
/usr/local/lib64/libstdc++.so
/usr/local/lib64/libstdc++.so.6.0.29-gdb.py
/usr/share/gdb/auto-load/usr/lib/libstdc++.so.6.0.19-gdb.py
/usr/share/gdb/auto-load/usr/lib/libstdc++.so.6.0.19-gdb.pyc
/usr/share/gdb/auto-load/usr/lib/libstdc++.so.6.0.19-gdb.pyo
/usr/share/gdb/auto-load/usr/lib64/libstdc++.so.6.0.19-gdb.py
/usr/share/gdb/auto-load/usr/lib64/libstdc++.so.6.0.19-gdb.pyc
/usr/share/gdb/auto-load/usr/lib64/libstdc++.so.6.0.19-gdb.pyo
/usr/lib64/libstdc++.so.6
/usr/lib64/libstdc++.so.6.0.19
/usr/lib64/libstdc++.so.6.0.29
/usr/lib64/libstdc++.so.6.0.20
```

可以看到，有更高的版本/usr/local/lib64/libstdc++.so.6.0.29

创建软链接

```
cp /usr/local/lib64/libstdc++.so.6.0.29 /usr/lib64/
rm libstdc++.so.6
ln -s libstdc++.so.6.0.29 libstdc++.so.6
```

再次检查动态库

```
strings /usr/lib64/libstdc++.so.6 | grep GLIBC
```

输出

```
GLIBCXX_3.4
GLIBCXX_3.4.1
GLIBCXX_3.4.2
GLIBCXX_3.4.3
GLIBCXX_3.4.4
GLIBCXX_3.4.5
GLIBCXX_3.4.6
GLIBCXX_3.4.7
GLIBCXX_3.4.8
GLIBCXX_3.4.9
GLIBCXX_3.4.10
GLIBCXX_3.4.11
GLIBCXX_3.4.12
GLIBCXX_3.4.13
GLIBCXX_3.4.14
GLIBCXX_3.4.15
GLIBCXX_3.4.16
GLIBCXX_3.4.17
GLIBCXX_3.4.18
GLIBCXX_3.4.19
GLIBCXX_3.4.20
GLIBCXX_3.4.21
GLIBCXX_3.4.22
GLIBCXX_3.4.23
GLIBCXX_3.4.24
GLIBCXX_3.4.25
GLIBCXX_3.4.26
GLIBCXX_3.4.27
GLIBCXX_3.4.28
GLIBCXX_3.4.29
GLIBC_2.2.5
GLIBC_2.3
GLIBC_2.14
GLIBC_2.6
GLIBC_2.4
GLIBC_2.16
GLIBC_2.17
GLIBC_2.3.2
```

可以看到，已经有了GLIBCXX_3.4.21，还是更高版本的一些库

到此问题解决

## 相关网址

> https://www.imqianduan.com/linux/gcc-update-libstdc.html