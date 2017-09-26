package Builder::Linux::Board::Artik::Artik710;

use v5.10;
use Carp;

use Moo;
extends 'Builder::Linux::Board::Artik';
with    'Builder::Linux::Feature::DeviceTree';

use Builder::Linux;

# make_ext4fs utility options

has make_modpart_opts => (
    is => 'lazy',
    builder => \&_build_make_modpart_opts,
);

##### Builders

sub _build_make_modpart_opts {
    my $self = shift;
    my $hash_opts = shift;
    my %opts_default = (
        block_size  => 4096 ,
        label       => "modules" ,
        size        => 32 . "M" ,
    );
    my @required_keys = (
        "output_file_path" ,
    );
    my $mod_path_postfix = "/lib/modules";

    if (defined $hash_opts) {
        foreach (@required_keys) {
            croak "Cannot build options for make_ext4fs utility!" if not exists $hash_opts->{$_}
        }
        $hash_opts->{source_dir_path} = $self->install_mod_path . $mod_path_postfix;
        foreach (keys %opts_default) {
            $hash_opts->{$_} = $opts_default{$_} if not exists $hash_opts->{$_}
        }
        return $hash_opts
    } else {
        croak "Cannot build options for make_ext4fs utility!"
    }
}

sub _build_make_ext4fs_opts {
    my $self = shift;
    my %translation_table = (
        block_size  => "-b" ,
        label       => "-L" ,
        size        => "-l" ,
    );
    my @opts = ();

    foreach (keys %translation_table) {
        push @opts, $translation_table{$_};
        push @opts, $self->make_modpart_opts->{$_}
    }
    push @opts, $self->make_modpart_opts->{output_file_path};
    push @opts, $self->make_modpart_opts->{source_dir_path};

    return @opts
}

##### Moo methods wrappers

around BUILDARGS => sub {
    my ($orig, $class, %args) = @_;
    $args{arch} = "arm64";
    $args{config_name} = "artik710_raptor_defconfig";
    $args{cross_compile} = "aarch64-linux-gnu-" if not exists $args{cross_compile};
    return $class->$orig(%args)
};

##### Board-specific subs

sub _board_specific_preparation {
    my $self = shift;
    my @config_opts = $self->_build_opts("config");
    push @config_opts, $self->config_name;
    system("make", @config_opts) == 0 or die fail "Failed create config!";
    say success "Created .config file";
    merge_kconfig(
        $self->build_path . "/.config",
        $self->_kfiles_path->{config} . "/board/unwds-artik-710/4.4.19-tizen/.config"
    );
    $self->_patch_kernel;
}

sub _board_specific_destruction {
    my $self = shift;
    $self->_revert_patches;
    $self->make_mrproper
}

##### Private methods

sub _prepare_repo {
    my $self = shift;
    my $repo = Git::Raw::Repository->open($self->kernel_src_path);
    foreach my $tag ($repo->tags) {
        if ($tag->name eq "origin/tizen_3.0") {
            $repo->checkout($tag);
            last;
        }
    }
}

sub _patch_kernel {
    my $self = shift;
    my $cmd_vcs = "git";
    $self->_prepare_repo;
    my @apply_patch_opts = ("apply", $self->_kfiles_path->{patch} . "/mali.patch");
    say info "Called kernel patching";
    system($cmd_vcs, @apply_patch_opts) == 0 or die fail "Failed patch kernel!";
    say success "Kernel patched!"
}

sub _revert_patches {
    my $self = shift;
    my $cmd_vcs = "git";
    $self->_prepare_repo;
    my @revert_patch_opts = ("apply", "-R", $self->_kfiles_path->{patch} . "/mali.patch");
    system($cmd_vcs, @revert_patch_opts) == 0 or die "Failed reverting patches!";
    unlink "drivers/gpu/arm/mali400/r5p2_rel0/__malidrv_build_info.c"
}

##### Public methods

sub make_ext4fs_mod_part {
    my $self = shift;
    my $cmd = "make_ext4fs";
    my @opts = $self->_build_make_ext4fs_opts;

    system($cmd, @opts) == 0 or die "Failed build ext4fs image!";
}

1;
