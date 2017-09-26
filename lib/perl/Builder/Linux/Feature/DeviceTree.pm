package Builder::Linux::Feature::DeviceTree;

use v5.10;
use Moo::Role;

after BUILD => sub {
    my ($self, $args) = @_;
    my @default = @{ $self->__common_base_make_vars };
    $self->_build_opts->{dtbs} = [ @default ];
};

sub make_dtbs {
    my $self = shift;
    my ($cmd, $target) = ("make", "dtbs");
    my @opts = $self->_build_opts($target);

    use Data::Printer;
    p @opts;
    system($cmd, @opts) == 0 or die "Failed `make dtbs`!";
}

1;
