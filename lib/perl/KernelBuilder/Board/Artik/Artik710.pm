package KernelBuilder::Board::Artik::Artik710;

use Carp;

use Moo;
extends 'KernelBuilder::Board::Artik';

use KernelBuilder;

before BUILDARGS => sub {
    my ($origin, $class, %args) = @_;
    $args{arch} = "arm64";
    $args{config_name} = "artik710_raptor_defconfig";
    $args{cross_compile} = "aarch64-linux-gnu-" if not exists $args{cross_compile};
    return $class->$origin(%args)
};

sub _board_specific_preparation {
    my $self = shift;
    my @config_opts = ( $self->arch, $self->config_name );
    merge_kconfig(
        $self->kernel_src_path . "/.config",
        $self->_kpatch_path . "/board/unwds-artik-710/4.4.19-tizen/.config"
    );
    $self->_patch_kernel
}

sub _patch_kernel {
    my $self = shift;
    my $repo = Git::Raw::Repository->open($self->kernel_src_path);
    foreach my $tag ($repo->tags) {
        if ($tag->name eq "origin/tizen_3.0") {
            $repo->checkout($tag);
            last;
        }
    }
    my @apply_patch_opts =  ("apply",       $self->_kfiles_path->{patch} . "/mali.patch");
    my @revert_patch_opts = ("apply", "-R", $self->_kfiles_path->{patch} . "/mali.patch");
    system "git", @apply_patch_opts;
}

sub make_dtbs {
    my $self = shift;
    my $cmd = "make";
    my $target = "dtbs";
    my @opts = _build_opts($target);
    system $cmd, @opts;
}
