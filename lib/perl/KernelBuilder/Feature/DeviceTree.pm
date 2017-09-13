package KernelBuilder::Feature::DeviceTree;

use v5.10;
use Moo::Role;

around _build_make_targets_opts => sub {
	my ($sub, $self, @args) = @_;
    my $opts = $self->$sub(@args);
    use Data::Printer; p $self;
    my @default = @{$self->__common_base_make_vars};
    $opts->{dtbs} = [ @default ];
    return $opts
};

sub make_dtbs {
    my $self = shift;
    my $cmd = "make";
    my $target = "dtbs";
    my @opts = $self->_build_opts($target);

    use Data::Printer; p @opts; p %{$self->_make_targets_opts};
    system($cmd, @opts) == 0 or die "Failed `make dtbs`!";
}

1;
