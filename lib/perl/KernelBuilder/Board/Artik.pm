package KernelBuilder::Board::Artik;

use v5.10;
use Carp;
use File::Path qw|make_path|;
use Cwd;
use DirHandle;

use Moo;

has _make_targets => (
    is => 'ro',
    builder => \&_build_make_targets
);

has _make_targets_jobnums => (
    is => 'ro',
    isa => sub {
        carp "$_[0] is not an HashRef!" unless (ref($_[0]) eq 'HASH')
    },
    builder => \&_build_make_targets_jobnums
);

has _make_opts => (
    is => 'lazy',
    builder => \&_build_make_opts,
);

has _make_targets_opts => (
    is => 'lazy',
    builder => \&_build_make_targets_opts,
);

has _kfiles_path => (
    is => 'rwp',
    builder => \&_build_kfiles_path
);

# Defaults

has __common_base_make_vars => (
    is => 'ro',
    default => sub { return [ "O", "ARCH", "CROSS_COMPILE" ] },
);

# Make options

has build_path => (
    is => 'ro',
    default => undef
);

has arch => (
    is => 'ro',
    default => "arm"
);

has cross_compile => (
    is => 'ro',
    default => "arm-linux-gnueabihf-"
);

has install_mod_path => (
    is => 'ro',
    default => ""
);

has config_name => (
    is => 'ro'
);

# Other options

has cross_compile_prefix => (
    is => 'ro',
    default => ""                           # Supposed to be in $PATH env var
);

has kernel_src_path => (
    is => 'ro',
    required => 1,
    builder => \&_build_kernel_src_path
);

# Builders

sub _build_make_targets_jobnums {
    # Returns hash which allows to look up to know whether target needs jobs param
    return {
        "Image"     => 1,
        "modules"   => 1,
    }
}

sub _build_make_targets {
    return [
        "Image",
        "prepare_modules",
        "modules",
        "modules_install"
    ]
}

sub _build_make_opts {
    my $self = shift;
    my $opts = {
        ARCH                => $self->arch ,
        CROSS_COMPILE       => $self->cross_compile_prefix . $self->cross_compile ,
        INSTALL_MOD_PATH    => $self->install_mod_path ,
        INSTALL_MOD_STRIP   => 1 ,
    };
    if (defined $self->build_path) {
        $opts->{O} = $self->build_path
    }
    return $opts;
}

sub _build_make_targets_opts {
    my $self = shift;
    my @default = @{$self->__common_base_make_vars};
    return {
        config          => [ "ARCH" ] ,
        Image           => [ @default ] ,
        prepare_modules => [ @default ] ,
        modules         => [ @default ] ,
        modules_install => [ @default, "INSTALL_MOD_PATH", "INSTALL_MOD_STRIP" ] ,
    }
}

sub _build_kfiles_path {
    my $self = shift;
    my $cwd = cwd;

    if ($cwd =~ /^(\/usr)?(\/(s)?bin)/) {
        return {
            patch   => "/etc/kernel_builder/kpatch" ,
            config  => "/etc/kernel_builder/kconfig" ,
        }
    } else {
        return {
            patch   => $cwd . "/kpatch" ,
            config  => $cwd . "/kconfig" ,
        }
    }
}

sub _build_kernel_src_path {
    my $self = shift;
    my $cwd = cwd;

    my $kernel_src_path = shift;
    return $kernel_src_path
}

#####

sub BUILD {
    my $self = shift;
    chdir($self->kernel_src_path);
    $self->_board_specific_preparation
}

sub _build_opts {
    my $self = shift;
    my $make_tgt = shift;
    my @opts = map {
        $_ . "=" . $self->_make_opts->{$_} if exists $self->_make_opts->{$_}
    } @{$self->_make_targets_opts->{$make_tgt}};
    push @opts, $make_tgt if not $make_tgt eq "config";
    push @opts, "-j8" if exists $self->_make_targets_jobnums->{$make_tgt};
    return @opts;
}

sub make_vmlinux {
    my $self = shift;
    use Data::Printer; p $self;
    my ($cmd, $target) = ("make", "Image");
    my @opts = $self->_build_opts($target);
    system($cmd, @opts) == 0 or die "Failed `make Image`!"
}

sub make_prepare_modules {
    my $self = shift;
    my ($cmd, $target) = ("make", "prepare_modules");
    my @opts = $self->_build_opts($target);
    system($cmd, @opts) == 0 or die "Failed `make prepare_modules`!"
}

sub make_modules {
    my $self = shift;
    my ($cmd, $target) = ("make", "modules");
    my @opts = $self->_build_opts($target);
    system($cmd, @opts) == 0 or die "Failed `make modules`!"
}

sub make_modules_install {
    my $self = shift;
    my ($cmd, $target) = ("make", "modules_install");
    make_path($self->install_mod_path);
    my @opts = $self->_build_opts($target);
    system($cmd, @opts) == 0 or die "Failed `make modules_install`!"
}

sub make_modules_partition {
    my $self = shift;
    my $cmd = "make_ext4fs";

}

1;
